from concurrent.futures import thread
from sqlite3 import OperationalError
import websockets
import asyncio
from abc import abstractmethod
from sqlalchemy_utils import database_exists
import json
import os
import threading
import time
import queue
import requests
from web import DATABASE_URL, datab
from web.db import Markets, Coins, Price, PerpetualPrice

# ------------- Exchange Class -----------------

class Exchange:
    def __init__(self, market_name, market_stream):
        self.queue = queue.Queue()
        sesh = datab.session()
        self.market_stream = market_stream
        self.market = sesh.query(Markets).filter_by(name=market_name).first()
        if self.market == None:
            new_market = Markets(name=market_name)
            sesh.add(new_market)
            self.safe_commit(sesh)
            self.market = new_market
            
        t = threading.Thread(target=self.between_callback)
        t.start()

    async def listen(self):
        async with websockets.connect(self.market_stream) as ws:
            await self._on_open_fcn(ws)
            while True:
                msg = json.loads(await ws.recv())
                await self._on_messagefcn(ws, msg)

    def safe_commit(self, sess):
        while True:
            try:
                sess.commit()
                sess.close()
                break
            except OperationalError:
                sess.rollback()

    def between_callback(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.listen())
        loop.close()

    @abstractmethod
    def _on_messagefcn(self, ws, message):
        pass
    
    async def _on_open_fcn(self, ws):
        pass
    
    def _add_to_database(self):
        while True:
            data = self.queue.get()
            sesh = datab.session()
            coin = sesh.query(Coins).filter_by(name=data["coin"]).first()
            if coin != None:
                price = sesh.query(Price).filter_by(coin_id=coin.id, market_id=data["market_id"]).first()
                if price != None:
                    price.bid = data["bid"]
                    price.ask = data["ask"]
                else:
                    sesh.add(Price(coin_id=coin.id,
                                        market_id=data["market_id"],
                                        bid=data["bid"],
                                        ask=data["ask"]))
            else:
                sesh.add(Coins(name=data["coin"]))
            self.safe_commit(sesh)

# All available MarketPlace
class Binance(Exchange):
    def __init__(self):
        super().__init__("binance", "wss://stream.binance.com:9443/ws/!bookTicker")
        
    async def _on_messagefcn(self, ws, data):
        self.queue.put({"coin" : data["s"],
                        "market_id" : self.market.id,
                        "bid" : data["b"],
                        "ask" : data["a"]})

class CryptoCom(Exchange):
    def __init__(self):
        super().__init__("crypto_com", "wss://stream.crypto.com/v2/market")

    async def _on_open_fcn(self, ws):
        time.sleep(1)
        request = {
            "id": 11,
            "method": "subscribe",
            "params": {
                "channels": ["ticker"]
            },
        }
        await ws.send(json.dumps(request))

    async def _on_messagefcn(self, ws, data):
        if "method" in data and data["method"] == "public/heartbeat":
            await ws.send(json.dumps({
                "id" : data["id"],
                "method" : "public/respond-heartbeat",
                }))
        elif "result" in data:
            self.queue.put({"coin" : data["result"]["instrument_name"].replace("_", ""),
                            "market_id" : self.market.id,
                            "bid" : data["result"]["data"][0]["b"],
                            "ask" : data["result"]["data"][0]["k"]})
            

# ----------------- FUTURES -------------------------------------
class FuturesMixin:
    def _add_to_database(self):
        while True:
            sesh = datab.session()
            data = self.queue.get()
            coin = sesh.query(Coins).filter_by(name=data["coin"]).first()
            if coin != None:
                price = sesh.query(PerpetualPrice).filter_by(coin_id=coin.id, market_id=self.market.id).first()
                if price != None:
                    price.price = float(data["price"])
                    price.funding_rate = float(data["funding_rate"])
                else:
                    sesh.add(PerpetualPrice(coin_id=coin.id,
                                                market_id=self.market.id,
                                                price=float(float(data["price"])),
                                                funding_rate=float(data["funding_rate"])))
            else:
                sesh.add(Coins(name=data['coin']))
            self.safe_commit(sesh)

    def _sync_funding_rate(self, url, market_id, interval):
        time.sleep(10)
        while True:
            sess = datab.session()
            perp_price = sess.query(PerpetualPrice).all()
            for price in perp_price:
                price = sess.query(PerpetualPrice).filter_by(coin_id=price.coin_id, market_id=market_id).first()
                coin_name = sess.query(Coins).get(price.coin_id).name
                data = json.loads(requests.get(url, params={"symbol" : str(coin_name)}).text)
                price.cum_7_day = sum([float(i["fundingRate"]) for i in data[-21:0:-1]])
                price.cum_30_day = sum([float(i["fundingRate"]) for i in data[-90:0:-1]])
            self.safe_commit(sess)
            time.sleep(interval)
            

class BinanceFutures(FuturesMixin, Exchange):
    def __init__(self):
        self.url = "https://fapi.binance.com/fapi/v1/fundingRate"
        self.INTERVAL = 8*3600
        super().__init__("binance_futures", "wss://fstream.binance.com/ws/!markPrice@arr@1s")
        threading.Thread(target=self._sync_funding_rate, args=(self.url, self.market.id, self.INTERVAL)).start()

    async def _on_messagefcn(self, ws, data):
        for i in range(len(data)):
            self.queue.put({"coin" : data[i]['s'],
                            "market_id" : self.market.id,
                            "price" : data[i]["p"],
                            "funding_rate" : data[i]["r"]})

# ------------- Core Data Class -----------------
class CoreData:
    def __init__(self) -> None:
        self.status = "online"
        self.exchanges = []
        if not database_exists(DATABASE_URL.replace("../", "")):
            datab.create_all()
            print("Database has just been created")
            print("""
            ----------DISCLAIMER----------
            Since Database Has just been created, you might need to restart
            the app a 2-3 times because there's a lot of data inserted into
            the sqlite at first and might cause some SQLite database lock.
            ----------DISCLAIMER----------
            """)
            self.status = "restart"
        self._initialize()

    def _initialize(self):
        try:
            for cls in Exchange.__subclasses__():
                obj = cls()
                self.exchanges.append(obj)
                threading.Thread(target=obj._add_to_database).start()
        except Exception:
            os._exit(0)

    def get_all_spot_data(self, sess):
        all_price = sess.query(Price).all()
        return all_price

    def get_all_futures_data(self, sess):
        return sess.query(PerpetualPrice).all()
    
    def get_all_data(self, sess):
        all_price = sess.query(Price).all()
        all_futures_data = sess.query(PerpetualPrice).all()
        return all_price, all_futures_data
    
    def search_spot_data(self, coin_name:str):
        sess = datab.session()
        while True:
            try:
                coin = sess.query(Coins).filter_by(name=coin_name).first()
                if coin != None:
                    spot = sess.query(Price).filter_by(coin_id=coin.id).all()
                    lst = []
                    for i in spot:
                        lst.append({"price" : i.ask, "market" : i.market.name})
                    return lst
            except OperationalError:
                continue

    def get_all_potential_arbitrage(self, sess, percentage_diff=0.05):
        data = []
        for coin in sess.query(Coins).all():
            price_value = []
            for market in sess.query(Markets).all():
                price = sess.query(Price).filter_by(coin_id=coin.id, market_id=market.id).first()
                if price != None:
                    price_value.append({"market_id": price.market.id, "price_sell": price.bid, "price_buy": price.ask})
            # Find the most price difference
            buy_price = min([price["price_buy"] for price in price_value], default=-1)
            sell_price = max([price["price_sell"] for price in price_value], default=-1)
            if sell_price <= buy_price or sell_price < buy_price*(1+percentage_diff):
                continue
            dict = {"coin_id": coin.id, "buy_at" : [], "sell_at" : []}
            for price in price_value:
                if price["price_buy"] == buy_price:
                    dict["buy_at"].append({"market_id" : price["market_id"], "price" : price["price_buy"]})
                if price["price_sell"] == sell_price:
                    dict["sell_at"].append({"market_id" : price["market_id"], "price" : price["price_sell"]})

            data.append(dict)
        return data
    
    def get_all_funding_rate(self, market_name, ticker):
        for exchange in self.exchanges:
            if exchange.market.name == market_name:
                data = json.loads(requests.get(exchange.url, params={"symbol" : str(ticker)}).text)
                return [float(i["fundingRate"]) for i in data]
