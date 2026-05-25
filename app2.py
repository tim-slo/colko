import sqlite3
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db2" / "social.db"

app = Flask(__name__, template_folder="template2", static_folder="static2")
app.config["SECRET_KEY"] = "zamenjaj-ta-kljuc-app2"


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
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS likes (
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, post_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (post_id) REFERENCES posts (id)
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
    with get_db() as conn:
        posts = conn.execute(
            """
            SELECT posts.*, users.username,
            (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count
            FROM posts
            JOIN users ON users.id = posts.user_id
            ORDER BY posts.created_at DESC
            """
        ).fetchall()
    return render_template("index.html", posts=posts)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if not username or not password:
            flash("Vpiši uporabniško ime in geslo.")
            return redirect(url_for("register"))

        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
            flash("Registracija je uspela. Zdaj se lahko prijaviš.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("To uporabniško ime je že zasedeno.")

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

        flash("Napačno uporabniško ime ali geslo.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/create", methods=["POST"])
def create_post():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    text = request.form["text"].strip()
    image_url = request.form.get("image_url", "").strip()
    if text:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO posts (user_id, text, image_url) VALUES (?, ?, ?)",
                (user["id"], text, image_url),
            )
    return redirect(url_for("index"))


@app.route("/api/post/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    user = current_user()
    if user is None:
        return jsonify({"error": "Za všečkanje se moraš prijaviti."}), 401

    with get_db() as conn:
        liked = conn.execute(
            "SELECT 1 FROM likes WHERE user_id = ? AND post_id = ?",
            (user["id"], post_id),
        ).fetchone()
        if liked:
            conn.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (user["id"], post_id))
            liked_now = False
        else:
            conn.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (user["id"], post_id))
            liked_now = True

        count = conn.execute("SELECT COUNT(*) AS total FROM likes WHERE post_id = ?", (post_id,)).fetchone()

    return jsonify({"liked": liked_now, "likes": count["total"]})


@app.route("/profile/<username>")
def profile(username):
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user is None:
            return redirect(url_for("index"))
        posts = conn.execute(
            """
            SELECT posts.*, users.username,
            (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count
            FROM posts
            JOIN users ON users.id = posts.user_id
            WHERE users.id = ?
            ORDER BY posts.created_at DESC
            """,
            (user["id"],),
        ).fetchall()
    return render_template("profile.html", profile_user=user, posts=posts)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
