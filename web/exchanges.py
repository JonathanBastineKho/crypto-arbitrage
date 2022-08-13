from websocket import WebSocketApp
from abc import abstractmethod
from sqlalchemy_utils import database_exists
import json
import threading
import time
from web import DATABASE_URL, db
from web.db import Markets, Coins, Price, PerpetualPrice

# ------------- Exchange Class -----------------

class Exchange(WebSocketApp):
    socket_message = None
    def __init__(self, market_name, market_stream):
        self.market_name = market_name
        self.market_stream = market_stream
        self.market = Markets.query.filter_by(name=self.market_name).first()
        super().__init__(self.market_stream,
                         on_open= lambda self : self._on_openfcn(),
                         on_message= lambda self, message : self._on_messagefcn(message),
                         on_error= lambda self, error : self._on_errorfcn(error),
                         on_close= lambda self : self._on_closefcn()
                        )
        exchange_socket = threading.Thread(target=self.run_forever)
        exchange_socket.start()

        if self.market == None:
            new_market = Markets(name=self.market_name)
            db.session.add(new_market)
            db.session.commit()
            self.market = new_market

    @abstractmethod
    def _on_messagefcn(self, message):
        pass

    @staticmethod
    def _on_errorfcn(error):
        socket_message = error

    @staticmethod
    def _on_closefcn():
        socket_message = "Error"

    @staticmethod
    def _on_openfcn():
        socket_message = "connection opened"

# All available MarketPlace

class Binance(Exchange):
    def __init__(self):
        super().__init__("binance", "wss://stream.binance.com:9443/ws/!bookTicker")
        
    def _on_messagefcn(self, message):
        data = json.loads(message)
        coin = Coins.query.filter_by(name=data["s"]).first()
        if coin != None:
            price = Price.query.filter_by(coin_id=coin.id, market_id=self.market.id).first()
            if price != None:
                price.bid = data["b"]
                price.ask = data["a"]
            else:
                db.session.add(Price(coin_id=coin.id, market_id=self.market.id, bid=data["b"], ask=data["a"]))
        else:
            db.session.add(Coins(name=data["s"]))
        
        db.session.commit()

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
        instrument_name = data["result"]["instrument_name"].replace("_", "")
        coin = Coins.query.filter_by(name=instrument_name).first()
        if coin != None:
            price = Price.query.filter_by(coin_id=coin.id, market_id = self.market.id).first()
            if price != None:
                price.bid = data["result"]["data"][0]["b"]
                price.ask = data["result"]["data"][0]["k"]
            else:
                db.session.add(Price(coin_id=coin.id,
                                    market_id=self.market.id,
                                    bid=data["result"]["data"][0]["b"],
                                    ask=data["result"]["data"][0]["k"]))
        else:
            db.session.add(Coins(name=instrument_name))
        db.session.commit()

class BinanceFutures(Exchange):
    def __init__(self):
        super().__init__("binance_futures", "wss://fstream.binance.com/ws/!markPrice@arr@1s")
    
    def _on_messagefcn(self, message):
        data = json.loads(message)
        for i in range(len(data)):
            coin = Coins.query.filter_by(name=data[i]['s']).first()
            if coin != None:
                price = PerpetualPrice.query.filter_by(coin_id=coin.id, market_id=self.market.id).first()
                if price != None:
                    price.price = float(data[i]['p'])
                    price.funding_rate = float(data[i]['r'])
                else:
                    db.session.add(PerpetualPrice(coin_id=coin.id,
                                                  market_id=self.market.id,
                                                  price=float(data[i]['p']),
                                                  funding_rate=float(data[i]['r'])))
            else:
                db.session.add(Coins(name=data[i]['s']))
        db.session.commit()

# ------------- Core Data Class -----------------

class CoreData:
    def __init__(self) -> None:
        if not database_exists(DATABASE_URL):
            db.create_all()
        for cls in Exchange.__subclasses__():
            cls()
    def get_all_spot_data(self):
        all_price = Price.query.all()
        return all_price

    def get_all_futures_data(self):
        return PerpetualPrice.query.all()
    
    def get_all_data(self):
        all_price = Price.query.all()
        all_futures_data = PerpetualPrice.query.all()
        return all_price, all_futures_data
    
    def search_spot_data(self, coin_name:str):
        # Coin Search
        coin = Coins.query.filter_by(name=coin_name).first()
        if coin != None:
            spot = Price.query.filter_by(coin_id=coin.id).first()
            return spot
        return None

    def get_all_potential_arbitrage(self, percentage_diff=0.05):
        data = []
        for coin in Coins.query.all():
            price_value = []
            for market in Markets.query.all():
                price = Price.query.filter_by(coin_id=coin.id, market_id=market.id).first()
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