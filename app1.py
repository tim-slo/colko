import sqlite3
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db1" / "notes.db"

app = Flask(__name__, template_folder="template1", static_folder="static1")
app.config["SECRET_KEY"] = "zamenjaj-ta-kljuc-app1"


def get_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


@app.route("/")
def index():
    search = request.args.get("search", "").strip()
    with get_db() as conn:
        if search:
            notes = conn.execute(
                """
                SELECT * FROM notes
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY created_at DESC
                """,
                (f"%{search}%", f"%{search}%"),
            ).fetchall()
        else:
            notes = conn.execute("SELECT * FROM notes ORDER BY created_at DESC").fetchall()
    return render_template("index.html", notes=notes, search=search)


@app.route("/add", methods=["POST"])
def add_note():
    title = request.form["title"].strip()
    content = request.form["content"].strip()
    if title and content:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO notes (title, content) VALUES (?, ?)",
                (title, content),
            )
    return redirect(url_for("index"))


@app.route("/edit/<int:note_id>", methods=["GET", "POST"])
def edit_note(note_id):
    with get_db() as conn:
        note = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if note is None:
            return redirect(url_for("index"))

        if request.method == "POST":
            title = request.form["title"].strip()
            content = request.form["content"].strip()
            conn.execute(
                "UPDATE notes SET title = ?, content = ? WHERE id = ?",
                (title, content, note_id),
            )
            return redirect(url_for("index"))

    return render_template("edit.html", note=note)


@app.route("/delete/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    with get_db() as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    return redirect(url_for("index"))


@app.route("/api/notes")
def api_notes():
    with get_db() as conn:
        notes = conn.execute("SELECT * FROM notes ORDER BY created_at DESC").fetchall()
    return jsonify([dict(note) for note in notes])


@app.route("/api/note/<int:note_id>/preview")
def api_note_preview(note_id):
    with get_db() as conn:
        note = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if note is None:
        return jsonify({"error": "Zapisek ne obstaja."}), 404
    return jsonify({"title": note["title"], "content": note["content"]})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
