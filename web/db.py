from web import db

class Coins(db.Model):
    __tablename__ = "CoinList"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    price = db.relationship("Price", back_populates="coin")

class Markets(db.Model):
    __tablename__ = "MarketList"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    price = db.relationship("Price", back_populates="market")

class Price(db.Model):
    __tablename__ = "PriceList"
    id = db.Column(db.Integer, primary_key=True)
    coin = db.relationship("Coins", back_populates="price")
    coin_id = db.Column(db.Integer, db.ForeignKey('CoinList.id'))
    market = db.relationship("Markets", back_populates="price")
    market_id = db.Column(db.Integer, db.ForeignKey('MarketList.id'))
    bid = db.Column(db.Float, nullable=False)
    ask = db.Column(db.Float, nullable=False)



        