from cmath import log
from web import app, socketio, core_data, BINANCE_API_KEY, BINANCE_PRIVATE_KEY, datab
from flask import render_template, jsonify, request, flash, redirect, url_for
import time
import hmac
import requests
import hashlib
from urllib.parse import urlencode
from sqlalchemy.event.api import listen
from flask_login import login_user, login_required, current_user, logout_user
from web import login_manager, bcrypt
from web.db import Price, PerpetualPrice, User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route("/spot-arbitrage")
def spot_arbitrage():
    return render_template("index.html", title="Spot - Spot Arbitrage")

@app.route("/")
def futures_arbitrage():
    return render_template("spot_futures_arbitrage.html", title="Spot - Futures Arbitrage")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('futures_arbitrage'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        if User.query.filter_by(email=email).first() == None and User.query.filter_by(username=username).first() == None:
            user = User(username=username,
            email=email, 
            password=bcrypt.generate_password_hash(request.form["password"], 13, prefix=b"2b"))
            datab.session.add(user)
            datab.session.commit()
            login_user(user)
            return redirect(url_for('futures_arbitrage'))
        elif User.query.filter_by(email=email).first() != None:
            flash("You already create this email")
        elif User.query.filter_by(username=username).first() != None:
            flash("You already create this username")
        return redirect(url_for('login'))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        print("executed")
        user = User.query.filter_by(username=request.form["username"]).first()
        if user != None and bcrypt.check_password_hash(pw_hash=user.password, password=request.form["username"]):
            login_user(user)
            return redirect(url_for('futures_arbitrage'))
        else:
            flash("username/email or password doesn't match")
            return redirect(url_for('login'))

    return render_template("login.html")

@app.route("/test/<market>/<ticker>")
def test(market, ticker):
    return jsonify(core_data.get_all_funding_rate(market, ticker))

def spot_price_emission(mapper, connection, target):
    try:
        data = {
            "coin" : target.coin.name,
            "market" : target.market.name,
            "bid" : float(target.bid),
            "ask" : float(target.ask)
        }
        socketio.emit('spot_data', data)
    except AttributeError:
        pass

def futures_price_emission(mapper, connection, target):
    try:
        spot_prices = core_data.search_spot_data(target.coin.name)
        for price in spot_prices:
            data = {
                "coin" : target.coin.name,
                "futures_price" : float(target.price),
                "futures_market" : target.market.name,
                "funding_rate" : float(target.funding_rate),
                "spot_price" : float(price["price"]),
                "spot_market" : price["market"],
                "cum_7_day" : float(target.cum_7_day) if target.cum_7_day != None else 0,
                "cum_30_day" : float(target.cum_30_day) if target.cum_30_day != None else 0,
            }
            socketio.emit('arbitrage_data', data)
    except AttributeError:
        pass

def listen_to_database():
    listen(Price, 'after_update', spot_price_emission)
    listen(Price, 'after_insert', spot_price_emission)
    listen(PerpetualPrice, 'after_update', futures_price_emission)
    listen(PerpetualPrice, 'after_insert', futures_price_emission)