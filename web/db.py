from web import datab
from flask_login import UserMixin

class Coins(datab.Model):
    __tablename__ = "CoinList"
    __bind_key__ = "market"
    id = datab.Column(datab.Integer, primary_key=True)
    name = datab.Column(datab.String(250), nullable=False)
    price = datab.relationship("Price", back_populates="coin")
    perp_price = datab.relationship("PerpetualPrice", back_populates="coin")

class Markets(datab.Model):
    __tablename__ = "MarketList"
    __bind_key__ = "market"
    id = datab.Column(datab.Integer, primary_key=True)
    name = datab.Column(datab.String(250), nullable=False)
    price = datab.relationship("Price", back_populates="market")
    perp_price = datab.relationship("PerpetualPrice", back_populates="market")
    asset = datab.relationship("Asset", back_populates="market")

class Price(datab.Model):
    __tablename__ = "PriceList"
    __bind_key__ = "market"
    id = datab.Column(datab.Integer, primary_key=True)
    coin = datab.relationship("Coins", back_populates="price")
    coin_id = datab.Column(datab.Integer, datab.ForeignKey('CoinList.id'))
    market = datab.relationship("Markets", back_populates="price")
    market_id = datab.Column(datab.Integer, datab.ForeignKey('MarketList.id'))
    bid = datab.Column(datab.Float, nullable=False)
    ask = datab.Column(datab.Float, nullable=False)

class PerpetualPrice(datab.Model):
    __tablename__ = "PerpetualPriceList"
    __bind_key__ = "market"
    id = datab.Column(datab.Integer, primary_key=True)
    coin = datab.relationship("Coins", back_populates="perp_price")
    coin_id = datab.Column(datab.Integer, datab.ForeignKey('CoinList.id'))
    market = datab.relationship("Markets", back_populates="perp_price")
    market_id = datab.Column(datab.Integer, datab.ForeignKey('MarketList.id'))
    price = datab.Column(datab.Float, nullable=False)
    funding_rate = datab.Column(datab.Float, nullable=False)
    cum_7_day = datab.Column(datab.Float)
    cum_30_day = datab.Column(datab.Float)

class User(UserMixin, datab.Model):
    __tablename__ = "user"
    __bind_key__ = "user"
    id = datab.Column(datab.Integer, primary_key=True)
    email = datab.Column(datab.String(250), nullable=False)
    username = datab.Column(datab.String(250), nullable=False)
    password = datab.Column(datab.String(1000), nullable=False)
    asset = datab.relationship("Asset", back_populates="user")

class Asset(datab.Model):
    __tablename__ = "asset"
    __bind_key__ = "user"
    id = datab.Column(datab.Integer, primary_key=True)
    coin = datab.Column(datab.String(250), nullable=False)
    market = datab.relationship("Markets", back_populates="asset")
    market_id = datab.Column(datab.Integer, datab.ForeignKey("MarketList.id"))
    user = datab.relationship("User", back_populates="asset")
    user_id = datab.Column(datab.Integer, datab.ForeignKey("user.id"))
    value = datab.Column(datab.Float, nullable=False)