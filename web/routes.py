from web import app, socketio, core_data
from flask import render_template
import time

@app.route("/")
def index():
    return render_template("index.html")

def background_thread():
    while True:
        prices = core_data.get_all_data()
        for i in range(len(prices)):
            data = {
                "coin" : prices[i].coin.name,
                "market" : prices[i].market.name,
                "bid" : prices[i].bid,
                "ask" : prices[i].ask,
            }
            socketio.emit('my_response', data)
        time.sleep(0.1)

@socketio.on('connect')
def handle_connection():
    socketio.start_background_task(background_thread)