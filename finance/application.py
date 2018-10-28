import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""


    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure the user inputs a symbol
        symbol = request.form.get("symbol").upper()
        if not symbol:
            return apology("must provide a symbol", 403)

        # ensure number of shares is submitted
        shares = request.form.get("shares")
        if not shares:
            return apology("must provide number of shares", 403)


        # do a try except for handling negative values or empty spaces in shares input box
        try:
            shares = int(shares)
            if shares < 0:
                return apology("Enter a positive integer for shares", 403)
        except ValueError:
            return apology("No empty spaces allowed enter a positive integer", 403)

        #  call lookup in helpers.py to look up a stock’s current price.
        stockPriceDetail = lookup(symbol)

        # render apology for invalid symbol input by user
        if stockPriceDetail == None:
            return apology("Invalid symbol", 403)
        else:
            price = stockPriceDetail["price"]

        # calculate the total price of the number of shares
        totalCost = price * shares
        print(totalCost)


        # based on user's input check if they have enough cash to buy stocks
        rows = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        print(rows)

        cash = rows[0] ["cash"]

        # Check for sufficient cash
        if cash < totalCost:
            return apology("you have insufficient cash balance", 403)

        balance = cash - totalCost

        # insert row in transactions table
        result = db.execute("""insert into transactions
                               (user_id,stock_code,stock_quantity,stock_price,
                               start_balance,end_balance,transaction_type)
                               values(:userid, :symbol, :shares, :price, :cash,
                               :balance,:ttype)""",
                               userid=session["user_id"],shares=shares,
                               symbol=symbol,price=price,
                               cash=cash,balance=balance,ttype="BOUGHT")

        # update users balance
        result = db.execute("update users set cash = :balance where id = :userid",
                              userid=session["user_id"],balance=balance)

        # Redirect user to index page
        return redirect("/")

    else:
        symbol = request.args.get('symbol')
        return render_template("buy.html",symbol=symbol)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
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
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        symbol = request.form.get("symbol")

        # if user does not input any symbol
        if not symbol:
            return apology("must provide symbol", 403)

        # call lookup function inside of helpers.py
        detail = lookup(symbol)

        # if an inavlid symbol is input by user return an apology
        if detail == None:
            return apology("invalid symbol", 403)
        else: # render price.html for valid symbol input and looup function returns a dict with price details
            return render_template("price.html",symbol=detail["symbol"],price=usd(detail["price"]))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # clear any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

       # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        # Ensure confirm password is same as password
        elif request.form.get("password") != request.form.get("passwordconfirm"):
            return apology("password must be confirmed", 403)
        # hash password using encrypt function
        password = generate_password_hash(request.form.get("password"))

        # save the registered user to db
        result = db.execute("INSERT INTO users(username,hash) VALUES(:username,:hash)",
                             username=request.form.get("username"),hash=password)
        # if user already exists in db
        if not result:
            return apology("username already exists")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        print("Executed select statement to query the user in db")
        # Once user is registered successfully log them in automatically by storing their id in session
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
