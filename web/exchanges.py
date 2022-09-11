from websocket import WebSocketApp
from abc import abstractmethod
from sqlalchemy_utils import database_exists
import json
import requests, os
import threading
import time
from web import DATABASE_URL, datab
from web.db import Markets, Coins, Price, PerpetualPrice

# ------------- Exchange Class -----------------

class Exchange(WebSocketApp):
    socket_message = None
    def __init__(self, market_name, market_stream):
        sesh = datab.session()
        self.market_stream = market_stream
        self.market = sesh.query(Markets).filter_by(name=market_name).first()
        if self.market == None:
            new_market = Markets(name=market_name)
            sesh.add(new_market)
            sesh.commit()
            sesh.close()
            self.market = new_market
        super().__init__(self.market_stream,
                         on_open= lambda self : self._on_openfcn(),
                         on_message= lambda self, message : self._on_messagefcn(message),
                         on_error= lambda self, error : self._on_errorfcn(error),
                         on_close= lambda self : self._on_closefcn()
                        )
        exchange_socket = threading.Thread(target=self.run_forever)
        exchange_socket.start()

    @abstractmethod
    def _on_messagefcn(self, message):
        pass

    @staticmethod
    def _on_errorfcn(error):
        Exchange.socket_message = error

    @staticmethod
    def _on_closefcn():
        Exchange.socket_message = "Error"

    @staticmethod
    def _on_openfcn():
        Exchange.socket_message = "connection opened"

# All available MarketPlace

class Binance(Exchange):
    def __init__(self):
        super().__init__("binance", "wss://stream.binance.com:9443/ws/!bookTicker")
        
    def _on_messagefcn(self, message):
        data = json.loads(message)
        sesh = datab.session()
        coin = sesh.query(Coins).filter_by(name=data["s"]).first()
        if coin != None:
            price = sesh.query(Price).filter_by(coin_id=coin.id, market_id=self.market.id).first()
            if price != None:
                price.bid = data["b"]
                price.ask = data["a"]
            else:
                sesh.add(Price(coin_id=coin.id, market_id=self.market.id, bid=data["b"], ask=data["a"]))
        else:
            sesh.add(Coins(name=data["s"]))
        
        sesh.commit()
        sesh.close()

class CryptoCom(Exchange):
    def __init__(self):
        request = {
            "id": 11,
            "method": "subscribe",
            "params": {
                "channels": ["ticker"]
            },
        }
        super().__init__("crypto_com", "wss://stream.crypto.com/v2/market")
        time.sleep(1)
        self.send(json.dumps(request))

    def _on_messagefcn(self, message):
        data = json.loads(message)
        sesh = datab.session()
        instrument_name = data["result"]["instrument_name"].replace("_", "")
        coin = sesh.query(Coins).filter_by(name=instrument_name).first()
        if coin != None:
            price = sesh.query(Price).filter_by(coin_id=coin.id, market_id = self.market.id).first()
            if price != None:
                price.bid = data["result"]["data"][0]["b"]
                price.ask = data["result"]["data"][0]["k"]
            else:
                sesh.add(Price(coin_id=coin.id,
                                    market_id=self.market.id,
                                    bid=data["result"]["data"][0]["b"],
                                    ask=data["result"]["data"][0]["k"]))
        else:
            sesh.add(Coins(name=instrument_name))
        sesh.commit()
        sesh.close()

# ----------------- FUTURES -------------------------------------
class FuturesMixin:
    def _sync_funding_rate(self, url, market_id, interval):
        sess = datab.session()
        while True:
            perp_price = sess.query(PerpetualPrice).all()
            for price in perp_price:
                price = sess.query(PerpetualPrice).filter_by(coin_id=price.coin_id, market_id=market_id).first()
                coin_name = sess.query(Coins).get(price.coin_id).name
                data = json.loads(requests.get(url, params={"symbol" : str(coin_name)}).text)
                price.cum_7_day = sum([float(i["fundingRate"]) for i in data[-21:0:-1]])
                price.cum_30_day = sum([float(i["fundingRate"]) for i in data[-90:0:-1]])
            sess.commit()
            time.sleep(interval)
            

class BinanceFutures(Exchange, FuturesMixin):
    url = "https://fapi.binance.com/fapi/v1/fundingRate"
    INTERVAL = 8*3600
    def __init__(self):
        super().__init__("binance_futures", "wss://fstream.binance.com/ws/!markPrice@arr@1s")
        threading.Thread(target=self._sync_funding_rate, args=(BinanceFutures.url, self.market.id, BinanceFutures.INTERVAL)).start()

    def _on_messagefcn(self, message):
        data = json.loads(message)
        sesh = datab.session()
        for i in range(len(data)):
            coin = sesh.query(Coins).filter_by(name=data[i]['s']).first()
            if coin != None:
                price = sesh.query(PerpetualPrice).filter_by(coin_id=coin.id, market_id=self.market.id).first()
                if price != None:
                    price.price = float(data[i]['p'])
                    price.funding_rate = float(data[i]['r'])
                else:
                    sesh.add(PerpetualPrice(coin_id=coin.id,
                                                  market_id=self.market.id,
                                                  price=float(data[i]['p']),
                                                  funding_rate=float(data[i]['r'])))
            else:
                sesh.add(Coins(name=data[i]['s']))
        sesh.commit()
        sesh.close()

# ------------- Core Data Class -----------------

class CoreData:
    def __init__(self) -> None:
        self.status = "online"
        if not database_exists(DATABASE_URL.replace("../", "")):
            datab.create_all()
            print("Database has just been created")
            self.status = "restart"
        
        self._initialize()

    def _initialize(self):
        try:
            for cls in Exchange.__subclasses__():
                cls()
        except:
            print("try running the app again")
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
    
    def search_spot_data(self, coin_name:str, sess):
        # Coin Search
        coin = sess.query(Coins).filter_by(name=coin_name).first()
        if coin != None:
            spot = sess.query(Price).filter_by(coin_id=coin.id).first()
            return spot
        return None

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