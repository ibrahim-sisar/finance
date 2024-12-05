import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from helpers import apology, login_required, lookup, usd
dt = datetime.datetime.now()

# MSFT 400
# AAPL 200
# GOOG 100
# AMZN 100
# TSLA 200
# META 500
# NFLX 600
# NVDA 100
# JNJ  100

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    totle = 0
    arr = []
    user_data = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    quote_dat = db.execute("SELECT * FROM quote WHERE user_id = ?;", session["user_id"])
    for i in quote_dat:
        print(i['name'])
        arr.append(lookup(i['name'])['price'])
        totle += (lookup(i['name'])['price'] * i['shares'])
    data2 = zip(quote_dat, arr)
    return render_template("index.html", data=[user_data, data2, totle])


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == 'POST':
        if not request.form.get("symbol"):
            return apology("MISSING symbol", 400)
        if not request.form.get("shares"):
            return apology("MISSING shares", 400)
        if int(request.form.get("shares")) < 1:
            return apology("too few shares", 400)
        sym = lookup(request.form.get("symbol"))
        print(sym['price'])
        sym_price = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        price_sum = float(sym['price'])*int(request.form.get("shares"))
        if (float(sym['price'])*int(request.form.get("shares"))) > int(sym_price[0]['cash']):
            return apology("can't afford", 400)
        if sym != None:
            db.execute("UPDATE users SET cash = cash - ? WHERE id = ?;",
                       price_sum, session["user_id"])
            quote_dat = db.execute("SELECT * FROM quote WHERE user_id = ? AND name = ?;",
                                   session["user_id"], request.form.get("symbol"))
            if len(quote_dat) != 0:
                db.execute("UPDATE quote SET shares = shares + 1 WHERE user_id = ?;",
                           session["user_id"])
            else:
                db.execute("INSERT INTO quote (name,price,shares,user_id) VALUES (?,?,?,?);",
                           sym['symbol'], sym['price'], int(request.form.get("shares")), int(session["user_id"]))
            db.execute("INSERT INTO History (symbol,shares,price,transacted,user_id) VALUES (?,?,?,?,?);",
                       sym['symbol'], int(request.form.get("shares")), sym['price'], dt, int(session["user_id"]))
            return redirect('/')
        else:
            return apology("invalid symbol", 400)
    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    data = db.execute("SELECT * FROM History WHERE user_id = ?;", session["user_id"])
    return render_template("History.html", data=data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == 'POST':
        if not request.form.get("symbol"):
            return apology("MISSING symbol", 400)
        sym = lookup(request.form.get("symbol"))
        if sym != None:
            return render_template("quoted.html", txt=sym)
        else:
            return apology("invalid symbol", 400)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()
    if request.method == 'POST':
        name = request.form.get("username")
        passwrod = request.form.get("password")
        passwordag = request.form.get("confirmation")

        if not name:
            return apology("MISSING USERNAME", 400)
        elif not passwrod:
            return apology("MISSING PASSWORD", 400)
        elif passwrod != passwordag:
            print(passwrod)
            print(passwordag)
            return apology("PASSWORDS DON'T MATCH", 400)
        else:
            data = db.execute("SELECT username FROM users WHERE username = ?;", name)
            if len(data) == 0:
                password_hash = generate_password_hash(passwrod)
                db.execute("INSERT INTO users (username,hash) VALUES (?,?);", name, password_hash)
                data = db.execute("SELECT id FROM users WHERE username = ?;", name)
                session["user_id"] = data[0]["id"]
                return redirect("/")
            else:
                return apology("USERNAME TAKEN.", 400)

    return render_template("Register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # user_data=db.execute("SELECT * FROM users WHERE id = ?",session["user_id"])
    if request.method == 'POST':
        quote_dat = db.execute("SELECT * FROM quote WHERE user_id = ? AND name = ?;",
                               session["user_id"], request.form.get("symbol"))
        if not request.form.get("symbol"):
            print(request.form.get("symbol"))
            return apology("MISSING symbol", 400)
        elif len(quote_dat) == 0:
            return apology("symbol not owned", 400)
        elif not request.form.get("shares"):
            return apology("MISSING shares", 400)
        elif int(request.form.get("shares")) < 1:
            return apology("too few shares", 400)
        elif int(request.form.get("shares")) > quote_dat[0]['shares']:
            return apology("too many shares", 400)
        else:

            sym = lookup(request.form.get("symbol"))['price']*int(request.form.get("shares"))
            db.execute("UPDATE users SET cash = cash + ? WHERE id = ?;", sym, session["user_id"])
            if quote_dat[0]['shares'] == int(request.form.get("shares")):
                db.execute("DELETE FROM quote WHERE name = ? AND user_id = ?;",
                           request.form.get("symbol"), session["user_id"])
            else:
                db.execute("UPDATE quote SET shares = shares - ? WHERE user_id = ?;",
                           int(request.form.get("shares")), session["user_id"])
            db.execute("INSERT INTO History (symbol,shares,price,transacted,user_id) VALUES (?,?,?,?,?);", request.form.get(
                "symbol"), int(request.form.get("shares"))*-1, lookup(request.form.get("symbol"))['price'], dt, int(session["user_id"]))
            return redirect("/")

    elif request.method == 'GET':
        quote_dat = db.execute("SELECT * FROM quote WHERE user_id = ?;", session["user_id"])
        return render_template("sell.html", data=quote_dat)
