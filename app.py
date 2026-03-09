from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS targets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        target_hours INTEGER,
        completed_hours INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS visitors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT,
        visit_time TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():

    ip = request.remote_addr

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO visitors(ip,visit_time) VALUES (?,?)",
        (ip, datetime.now())
    )

    conn.commit()
    conn.close()

    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users(name,email,password) VALUES (?,?,?)",
            (name, email, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        user = cur.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()

        conn.close()

        if user:
            session["user_id"] = user["id"]
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":

        category = request.form["category"]
        target = request.form["target"]

        cur.execute("""
        INSERT INTO targets(user_id,category,target_hours,completed_hours)
        VALUES (?,?,?,0)
        """, (user_id, category, target))

        conn.commit()

    data = cur.execute(
        "SELECT * FROM targets WHERE user_id=?",
        (user_id,)
    ).fetchall()

    conn.close()

    return render_template("dashboard.html", data=data)


@app.route("/update/<int:id>")
def update_hours(id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE targets
    SET completed_hours = completed_hours + 1
    WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


@app.route("/admin")
def admin():

    conn = get_db()
    cur = conn.cursor()

    users = cur.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    visitors = cur.execute(
        "SELECT COUNT(*) FROM visitors"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        visitors=visitors
    )
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":

        category = request.form["category"]
        target = request.form["target"]

        cur.execute("""
        UPDATE targets
        SET category = ?, target_hours = ?
        WHERE id = ?
        """, (category, target, id))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    activity = cur.execute(
        "SELECT * FROM targets WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template("edit.html", activity=activity)

@app.route("/delete/<int:id>")
def delete(id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM targets WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")



if __name__ == "__main__":
    app.run(debug=True)