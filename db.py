from sqlalchemy import ForeignKey, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa
from dotenv import load_dotenv
import os

load_dotenv()

base = declarative_base()
engine = sa.create_engine(os.getenv("DATABASE_URL"))
base.metadata.bind = engine
session = orm.scoped_session(orm.sessionmaker(bind=engine))

class Coins(base):
    __tablename__ = "CoinList"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(250), nullable=False)
    price = orm.relationship("Price", uselist=False)

class Markets(base):
    __tablename__ = "MarketList"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(250), nullable=False)
    price = orm.relationship("Price", uselist=False)

class Price(base):
    __tablename__ = "PriceList"
    id = sa.Column(sa.Integer, primary_key=True)
    coin_id = sa.Column(sa.Integer, ForeignKey('CoinList.id'))
    market_id = sa.Column(sa.Integer, ForeignKey('MarketList.id'))
    bid = sa.Column(sa.Float, nullable=False)
    ask = sa.Column(sa.Float, nullable=False)