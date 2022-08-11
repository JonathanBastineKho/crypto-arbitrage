from socket import socket
from web import app, socketio, core_data
from flask import render_template
import time

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/spot-futures-arbitrage")
def potential_arbitrage():
    return render_template("spot_futures_arbitrage.html")

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

@socketio.on('connect')
def handle_connection():
    socketio.start_background_task(background_thread)