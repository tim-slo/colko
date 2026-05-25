import sqlite3
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db3" / "tasks.db"

app = Flask(__name__, template_folder="template3", static_folder="static3")
app.config["SECRET_KEY"] = "zamenjaj-ta-kljuc-app3"


def get_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'splošno',
                done INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


@app.route("/")
def index():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    category = request.args.get("category", "vse")
    with get_db() as conn:
        if category != "vse":
            tasks = conn.execute(
                "SELECT * FROM tasks WHERE user_id = ? AND category = ? ORDER BY done, created_at DESC",
                (user["id"], category),
            ).fetchall()
        else:
            tasks = conn.execute(
                "SELECT * FROM tasks WHERE user_id = ? ORDER BY done, created_at DESC",
                (user["id"],),
            ).fetchall()
        categories = conn.execute(
            "SELECT DISTINCT category FROM tasks WHERE user_id = ? ORDER BY category",
            (user["id"],),
        ).fetchall()
    return render_template("index.html", tasks=tasks, categories=categories, selected_category=category)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
            flash("Registracija je uspela.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Uporabniško ime je že zasedeno.")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
        flash("Napačna prijava.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/add", methods=["POST"])
def add_task():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    title = request.form["title"].strip()
    category = request.form.get("category", "splošno").strip() or "splošno"
    if title:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO tasks (user_id, title, category) VALUES (?, ?, ?)",
                (user["id"], title, category),
            )
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    user = current_user()
    if user:
        with get_db() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["id"]))
    return redirect(url_for("index"))


@app.route("/api/task/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id):
    user = current_user()
    if user is None:
        return jsonify({"error": "Nisi prijavljen."}), 401

    with get_db() as conn:
        task = conn.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user["id"]),
        ).fetchone()
        if task is None:
            return jsonify({"error": "Naloga ne obstaja."}), 404
        new_value = 0 if task["done"] else 1
        conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (new_value, task_id))
    return jsonify({"done": bool(new_value)})


@app.route("/api/stats")
def stats():
    user = current_user()
    if user is None:
        return jsonify({"error": "Nisi prijavljen."}), 401
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) AS total FROM tasks WHERE user_id = ?", (user["id"],)).fetchone()
        done = conn.execute(
            "SELECT COUNT(*) AS total FROM tasks WHERE user_id = ? AND done = 1",
            (user["id"],),
        ).fetchone()
    return jsonify({"total": total["total"], "done": done["total"]})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5002)
