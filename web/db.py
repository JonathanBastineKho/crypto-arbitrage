from web import base, sa
from sqlalchemy import ForeignKey, orm

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



        