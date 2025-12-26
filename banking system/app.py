from flask import Flask, request, redirect, session, render_template_string
import sqlite3

app = Flask(__name__)
app.secret_key = "bank_secret"

def db_conn():
    return sqlite3.connect("bank.db")

def init_db():
    db = db_conn()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        balance INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS beneficiaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner TEXT,
        beneficiary TEXT
    )
    """)

    db.commit()
    db.close()

init_db()

with open("templates.html") as f:
    TEMPLATE = f.read()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = db_conn()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        db.close()

        if user:
            session["user"] = email
            return redirect("/dashboard")

    return render_template_string(TEMPLATE, page="login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        db = db_conn()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO users VALUES (NULL,?,?,?,?)",
            (request.form["name"], request.form["email"], request.form["password"], 1000)
        )
        db.commit()
        db.close()
        return redirect("/")

    return render_template_string(TEMPLATE, page="register")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    db = db_conn()
    cur = db.cursor()
    cur.execute("SELECT balance FROM users WHERE email=?", (session["user"],))
    balance = cur.fetchone()[0]
    db.close()

    return render_template_string(TEMPLATE, page="dashboard", balance=balance)

@app.route("/beneficiary", methods=["GET", "POST"])
def beneficiary():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        db = db_conn()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO beneficiaries VALUES (NULL,?,?)",
            (session["user"], request.form["email"])
        )
        db.commit()
        db.close()

    db = db_conn()
    cur = db.cursor()
    cur.execute("SELECT beneficiary FROM beneficiaries WHERE owner=?", (session["user"],))
    data = cur.fetchall()
    db.close()

    return render_template_string(TEMPLATE, page="beneficiary", data=data)

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        receiver = request.form["receiver"]
        amount = int(request.form["amount"])

        db = db_conn()
        cur = db.cursor()
        cur.execute("SELECT balance FROM users WHERE email=?", (session["user"],))
        balance = cur.fetchone()[0]

        if balance >= amount:
            cur.execute("UPDATE users SET balance=balance-? WHERE email=?",
                        (amount, session["user"]))
            cur.execute("UPDATE users SET balance=balance+? WHERE email=?",
                        (amount, receiver))
            cur.execute("INSERT INTO transactions VALUES (NULL,?,?,?)",
                        (session["user"], receiver, amount))
            db.commit()

        db.close()
        return redirect("/dashboard")

    return render_template_string(TEMPLATE, page="transfer")

@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/")

    db = db_conn()
    cur = db.cursor()
    cur.execute("SELECT * FROM transactions WHERE sender=?", (session["user"],))
    data = cur.fetchall()
    db.close()

    return render_template_string(TEMPLATE, page="history", data=data)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
