from flask import Flask, render_template
import os
from dotenv import load_dotenv
from flask_socketio import SocketIO, send, emit
import sys
sys.path.append(os.path.join(os.path.dirname(sys.path[0]), 'core'))


load_dotenv()
app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

from app import routes