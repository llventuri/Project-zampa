from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Temporary storage (replace later with database)
current_user_id = 1

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            neighborhood TEXT,
            dog_name TEXT,
            dog_breed TEXT
        )
    """)

    # Posts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            neighborhood TEXT,
            time TEXT,
            type TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Get user data
        
        username = request.form.get("username")
        email = request.form.get("email")
        neighborhood = request.form.get("neighborhood")

        # Get dog data
        dog_name = request.form.get("dog_name")
        dog_breed = request.form.get("dog_breed")

        # Store it 

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (username, email, neighborhood, dog_name, dog_breed)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, neighborhood, dog_name, dog_breed))

        conn.commit()
        conn.close()

        return redirect(url_for("board"))

    return render_template("register.html")

@app.route("/success")
def success():
    return "<h2>Registration successful!</h2>"

@app.route("/about")
def about():
    return "<h2>About Zampa</h2>"

@app.route("/board", methods=["GET", "POST"])
def board():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        neighborhood = request.form.get("neighborhood")
        time = request.form.get("time")
        post_type = request.form.get("type")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO posts (title, description, neighborhood, time, type, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, description, neighborhood, time, post_type, current_user_id))

        conn.commit()
        conn.close()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    selected_neighborhood = request.args.get("neighborhood")

    if selected_neighborhood and selected_neighborhood != "":
        cursor.execute("""
            SELECT posts.*, users.username
            FROM posts
            JOIN users ON posts.user_id = users.id
            WHERE posts.neighborhood = ?
        """, (selected_neighborhood,))
    else:
        cursor.execute("""
            SELECT posts.*, users.username
            FROM posts
            JOIN users ON posts.user_id = users.id
        """)

    rows = cursor.fetchall()
    conn.close()

    posts = []
    for row in rows:
        posts.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "neighborhood": row[3],
            "time": row[4],
            "type": row[5],
            "user_id": row[6],
            "username": row[7]
        })

    return render_template(
        "board.html",
        posts=posts,
        selected_neighborhood=selected_neighborhood
    )

@app.route("/community")
def community():
    return "<h2>Community (coming soon)</h2>"

@app.route("/search")
def search():
    return "<h2>Search (coming soon)</h2>"

@app.route("/profile")
def profile():
    return "<h2>My Profile (coming soon)</h2>"

@app.route("/tokens")
def tokens():
    return "<h2>Tokens system (coming soon)</h2>"

init_db()

if __name__ == "__main__":
    app.run(debug=True)

