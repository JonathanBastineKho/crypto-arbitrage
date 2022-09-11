from web import datab

class Coins(datab.Model):
    __tablename__ = "CoinList"
    id = datab.Column(datab.Integer, primary_key=True)
    name = datab.Column(datab.String(250), nullable=False)
    price = datab.relationship("Price", back_populates="coin")
    perp_price = datab.relationship("PerpetualPrice", back_populates="coin")

class Markets(datab.Model):
    __tablename__ = "MarketList"
    id = datab.Column(datab.Integer, primary_key=True)
    name = datab.Column(datab.String(250), nullable=False)
    price = datab.relationship("Price", back_populates="market")
    perp_price = datab.relationship("PerpetualPrice", back_populates="market")

class Price(datab.Model):
    __tablename__ = "PriceList"
    id = datab.Column(datab.Integer, primary_key=True)
    coin = datab.relationship("Coins", back_populates="price")
    coin_id = datab.Column(datab.Integer, datab.ForeignKey('CoinList.id'))
    market = datab.relationship("Markets", back_populates="price")
    market_id = datab.Column(datab.Integer, datab.ForeignKey('MarketList.id'))
    bid = datab.Column(datab.Float, nullable=False)
    ask = datab.Column(datab.Float, nullable=False)

class PerpetualPrice(datab.Model):
    __tablename__ = "PerpetualPriceList"
    id = datab.Column(datab.Integer, primary_key=True)
    coin = datab.relationship("Coins", back_populates="perp_price")
    coin_id = datab.Column(datab.Integer, datab.ForeignKey('CoinList.id'))
    market = datab.relationship("Markets", back_populates="perp_price")
    market_id = datab.Column(datab.Integer, datab.ForeignKey('MarketList.id'))
    price = datab.Column(datab.Float, nullable=False)
    funding_rate = datab.Column(datab.Float, nullable=False)
    cum_7_day = datab.Column(datab.Float)
    cum_30_day = datab.Column(datab.Float)