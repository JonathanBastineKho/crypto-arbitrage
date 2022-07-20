from web import app, socketio
from flask import render_template
import time

@app.route("/")
def index():
    return render_template("index.html")

def background_thread():
    while True:
        socketio.emit('my_response', {"data": "test"})
        time.sleep(0.05)

@socketio.on('connect')
def handle_conection():
    socketio.start_background_task(background_thread)