from flask import Flask
import os
from dotenv import load_dotenv
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

load_dotenv()

app = Flask(__name__)
Bootstrap(app)
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL_USER = os.getenv("USER_DATABASE")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_PRIVATE_KEY = os.getenv("BINANCE_SECRET_KEY")
class DbConfig(object):
    SECRET_KEY = os.getenv("SECRET_KEY")
    FLASK_APP = "application.py"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_BINDS = {
        'market': DATABASE_URL,
        'user': DATABASE_URL_USER
    }
app.config.from_object(DbConfig)
csrf = CSRFProtect()
csrf.init_app(app)
bcrypt = Bcrypt(app)
datab = SQLAlchemy(app)
socketio = SocketIO(app, async_mode="threading")
login_manager = LoginManager()
login_manager.init_app(app)

from web.exchanges import CoreData
core_data = CoreData()
from web import routes
routes.listen_to_database()