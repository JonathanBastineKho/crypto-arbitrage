from flask import Flask
import os
from dotenv import load_dotenv
from flask_socketio import SocketIO
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa
load_dotenv()

base = declarative_base()
engine = sa.create_engine(os.getenv("DATABASE_URL"))
base.metadata.bind = engine
session = orm.scoped_session(orm.sessionmaker(bind=engine))
app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
socketio = SocketIO(app, async_mode="threading")


from web import routes
from web.exchanges import CoreData
core_data = CoreData()
