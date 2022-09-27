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

@app.route("/test/<market>/<ticker>")
def test(market, ticker):
    return jsonify(core_data.get_all_funding_rate(market, ticker))

def spot_price_emission(mapper, connection, target):
    try:
        data = {
            "coin" : target.coin.name,
            "market" : target.market.name,
            "bid" : float(target.bid),
            "ask" : float(target.ask)
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
                "futures_price" : float(target.price),
                "futures_market" : target.market.name,
                "funding_rate" : float(target.funding_rate),
                "spot_price" : float(price["price"]),
                "spot_market" : price["market"],
                "cum_7_day" : float(target.cum_7_day) if target.cum_7_day != None else 0,
                "cum_30_day" : float(target.cum_30_day) if target.cum_30_day != None else 0,
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
    socketio.start_background_task(balance_sync_background)