from websocket import WebSocketApp
from abc import abstractmethod
import json
import threading
import time
from db import *

# ------------- Exchange Class -----------------

class Exchange(WebSocketApp):
    def __init__(self, market_name, market_stream, request=None):
        self.socket_message = None
        self.market_name = market_name
        self.request = request
        self.market_stream = market_stream
        self.market = None
        super().__init__(self.market_stream,
                         on_open= lambda self : self.on_openfcn(),
                         on_message= lambda self, message : self.on_messagefcn(message),
                         on_error= lambda self, error : self.on_errorfcn(error),
                         on_close= lambda self : self.on_closefcn()
                        )
        exchange_socket = threading.Thread(target=self.run_forever)
        exchange_socket.start()
        if self.request != None:
            time.sleep(1)
            self.send(json.dumps(self.request))
        with session() as initial_session:
            self.market = initial_session.query(Markets).filter_by(name=self.market_name).first()
            if self.market == None:
                initial_session.add(Markets(name=self.market_name))
                initial_session.commit()
            
    @abstractmethod
    def on_messagefcn(self, message):
        pass

    def on_errorfcn(self, error):
        self.socket_message = error

    def on_closefcn(self):
        self.socket_message = "Error"

    def on_openfcn(self):
        self.socket_message = "connection opened"

# All available MarketPlace

class Binance(Exchange):
    def __init__(self):
        super().__init__("binance", "wss://stream.binance.com:9443/ws/!bookTicker")
        
    def on_messagefcn(self, message):
        data = json.loads(message)
        with session() as data_session:
            coin = data_session.query(Coins).filter_by(name=data["s"]).first()
            if coin != None:
                price = data_session.query(Price).filter_by(coin_id=coin.id, market_id=self.market.id).first()
                if price != None:
                    price.bid = data["b"]
                    price.ask = data["a"]
                else:
                    data_session.add(Price(coin_id=coin.id, market_id=self.market.id, bid=data["b"], ask=data["a"]))
            else:
                data_session.add(Coins(name=data["s"]))
            
            data_session.commit()

class CryptoCom(Exchange):
    def __init__(self):
        request = {
            "id": 11,
            "method": "subscribe",
            "params": {
                "channels": ["ticker"]
            },
        }
        super().__init__("crypto_com", "wss://stream.crypto.com/v2/market", request)

    def on_messagefcn(self, message):
        data = json.loads(message)
        with session() as data_session:
            instrument_name = data["result"]["instrument_name"].replace("_", "")
            coin = data_session.query(Coins).filter_by(name=instrument_name).first()
            if coin != None:
                price = data_session.query(Price).filter_by(coin_id=coin.id, market_id = self.market.id).first()
                if price != None:
                    price.bid = data["result"]["data"][0]["b"]
                    price.ask = data["result"]["data"][0]["k"]
                else:
                    data_session.add(Price(coin_id=coin.id,
                                     market_id=self.market.id,
                                     bid=data["result"]["data"][0]["b"],
                                     ask=data["result"]["data"][0]["k"]))
            else:
                data_session.add(Coins(name=instrument_name))
            data_session.commit()

# ------------- Create all MarketPlace Instance -----------------
# base.metadata.create_all() # if database hasn't been created yet

def get_all_data():
    for cls in Exchange.__subclasses__():
        cls()
