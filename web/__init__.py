from flask import Flask
import os
from dotenv import load_dotenv
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import sqlalchemy as sa
load_dotenv()

app = Flask(__name__)
Bootstrap(app)
DATABASE_URL = os.getenv("DATABASE_URL")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db = SQLAlchemy(app)

socketio = SocketIO(app, async_mode="threading")

from web.exchanges import CoreData
core_data = CoreData()
from web import routes

