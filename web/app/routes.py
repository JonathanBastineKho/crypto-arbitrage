from app import *

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on('connect')
def handle_conection(data):
    print("it works")

