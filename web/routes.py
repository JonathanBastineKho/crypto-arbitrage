from socket import socket
from web import app, socketio, core_data, BINANCE_API_KEY, BINANCE_PRIVATE_KEY
from flask import render_template, jsonify
import time
import hmac
import requests
import hashlib
from urllib.parse import urlencode

@app.route("/")
def index():
    return render_template("index.html", title="Spot - Spot Arbitrage")

@app.route("/spot-futures-arbitrage")
def potential_arbitrage():
    return render_template("spot_futures_arbitrage.html", title="Spot - Futures Arbitrage", _get_balance=jsonify({"test":"test"}))

def background_thread():
    while True:
        prices = core_data.get_all_spot_data()
        futures = core_data.get_all_futures_data()
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
            spot = core_data.search_spot_data(coin_name=coin_name)
            if spot != None:
                data = {
                    "coin" : coin_name,
                    "futures_price" : ft_price.price,
                    "spot_price" : spot.ask,
                    "futures_market" : ft_price.market.name,
                    "spot_market" : spot.market.name,
                    "funding_rate" : ft_price.funding_rate
                }
                socketio.emit('arbitrage_data', data)
        time.sleep(0.1)

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
        time.sleep(5)

@socketio.on('connect')
def handle_connection():
    socketio.start_background_task(background_thread)
    socketio.start_background_task(balance_sync_background)
