from web import app, socketio, core_data, BINANCE_API_KEY, BINANCE_PRIVATE_KEY, datab
from flask import render_template, jsonify
import time
import hmac
import requests
import hashlib
from urllib.parse import urlencode
from sqlalchemy.event.api import listen
from web.db import Price, PerpetualPrice

@app.route("/")
def index():
    return render_template("index.html", title="Spot - Spot Arbitrage")

@app.route("/spot-futures-arbitrage")
def potential_arbitrage():
    return render_template("spot_futures_arbitrage.html", title="Spot - Futures Arbitrage", _get_balance=jsonify({"test":"test"}))

def background_thread():
    sess = datab.session()
    while True:
        prices = core_data.get_all_spot_data(sess=sess)
        futures = core_data.get_all_futures_data(sess=sess)
        for i in range(len(prices)):
            data = {
                "coin" : prices[i].coin.name,
                "market" : prices[i].market.name,
                "bid" : prices[i].bid,
                "ask" : prices[i].ask,
            }
            socketio.emit('spot_data', data)
        for ft_price in futures:
            coin_name = ft_price.coin.name
            spot = core_data.search_spot_data(coin_name=coin_name,  sess=sess)
            if spot != None:
                data = {
                    "coin" : coin_name,
                    "futures_price" : ft_price.price,
                    "spot_price" : spot.ask,
                    "futures_market" : ft_price.market.name,
                    "spot_market" : spot.market.name,
                    "funding_rate" : ft_price.funding_rate,
                }
                socketio.emit('arbitrage_data', data)
        time.sleep(0.1)
def spot_price_emission(mapper, connection, target):
    try:
        data = {
            "coin" : target.coin.name,
            "market" : target.market.name,
            "bid" : target.bid,
            "ask" : target.ask
        }
        socketio.emit('spot_data', data)
    except AttributeError:
        pass

def futures_price_emission(mapper, connection, target):
    try:
        spot_prices = core_data.search_spot_data(target.coin.name)
        for price in spot_prices:
            data = {
                "coin" : target.coin.name,
                "futures_price" : target.price,
                "futures_market" : target.market.name,
                "funding_rate" : target.funding_rate,
                "spot_price" : price["price"],
                "spot_market" : price["market"],
                "cum_7_day" : target.cum_7_day,
                "cum_30_day" : target.cum_30_day
            }
            socketio.emit('arbitrage_data', data)
    except AttributeError:
        pass

def listen_to_database():
    listen(Price, 'after_update', spot_price_emission)
    listen(Price, 'after_insert', spot_price_emission)
    listen(PerpetualPrice, 'after_update', futures_price_emission)
    listen(PerpetualPrice, 'after_insert', futures_price_emission)

def balance_sync_background():
    ENDPOINT = "https://api.binance.com/sapi/v3/asset/getUserAsset"
    assets = ["USDT", "USD", "BUSD"]
    headers = {"X-MBX-APIKEY" : BINANCE_API_KEY}
    while True:
        user_asset = {}
        for asset in assets:
            params = {
                "timestamp" : int(time.time()*1000) - 1000,
                "asset" : asset
            }
            query_string = urlencode(params)
            params['signature'] = hmac.new(BINANCE_PRIVATE_KEY.encode('utf-8'), 
                                        query_string.encode('utf-8'), 
                                        hashlib.sha256).hexdigest()
            response = requests.post(ENDPOINT, headers=headers, params=params)
            value = 0 if not response.text.isdigit() else int(response.text)
            user_asset[asset] = value
        socketio.emit('user_balance', user_asset)
        time.sleep(30)

@socketio.on('connect')
def handle_connection():
    # socketio.start_background_task(background_thread)
    socketio.start_background_task(balance_sync_background)