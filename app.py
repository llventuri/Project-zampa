from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "1Donz57heSxD"

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE,
            password TEXT,
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
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        neighborhood = request.form.get("neighborhood")
        dog_name = request.form.get("dog_name")
        dog_breed = request.form.get("dog_breed")

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (username, email, password, neighborhood, dog_name, dog_breed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, email, hashed_password, neighborhood, dog_name, dog_breed))

            conn.commit()

            user_id = cursor.lastrowid
            session["user_id"] = user_id

            conn.close()
            return redirect(url_for("my_profile"))

        except sqlite3.IntegrityError:
            conn.close()
            return "<h2>Email already registered. Please use another one.</h2>"

    return render_template("register.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password): 
            session["user_id"] = user["id"]
            return redirect(url_for("my_profile"))
        else:
            return "<h2>Invalid email or password.</h2>"

    return render_template("login.html")

@app.route("/board", methods=["GET", "POST"])
def board():
    user_id = session.get("user_id")

    if user_id is None:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        neighborhood = request.form.get("neighborhood")
        time = request.form.get("time")
        post_type = request.form.get("type")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO posts (title, description, neighborhood, time, type, user_id)
            VALUES (?, ?, ?, ?, ?, ?) 
        """, (title, description, neighborhood, time, post_type, user_id))  

        conn.commit()
        conn.close()

    conn = get_db_connection()
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
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "neighborhood": row["neighborhood"],
            "time": row["time"],
            "type": row["type"],
            "user_id": row["user_id"],
            "username": row["username"]
        })

    return render_template(
        "board.html",
        posts=posts,
        selected_neighborhood=selected_neighborhood
    )

@app.route("/users")
def users_list():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    conn.close()

    users = []
    for row in rows:
        users.append({
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "neighborhood": row["neighborhood"],
            "dog_name": row["dog_name"],
            "dog_breed": row["dog_breed"]
        })

    return render_template("users.html", users=users)

@app.route("/user/<int:user_id>")
def user_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()

    if user_row is None:
        conn.close()
        return "<h2>User not found</h2>"

    cursor.execute("SELECT * FROM posts WHERE user_id = ?", (user_id,))
    post_rows = cursor.fetchall()
    conn.close()

    user = {
        "id": user_row["id"],
        "username": user_row["username"],
        "email": user_row["email"],
        "neighborhood": user_row["neighborhood"],
        "dog_name": user_row["dog_name"],
        "dog_breed": user_row["dog_breed"]
    }

    posts = []
    for row in post_rows:
        posts.append({
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "neighborhood": row["neighborhood"],
            "time": row["time"],
            "type": row["type"]
        })

    return render_template("user_profile.html", user=user, posts=posts)

@app.route("/community")
def community():
    return "<h2>Community (coming soon)</h2>"

@app.route("/search")
def search():
    username = request.args.get("username", "")
    dog_name = request.args.get("dog_name", "")
    neighborhood = request.args.get("neighborhood", "")

    conn = get_db_connection()

    users = conn.execute("""
        SELECT * FROM users
        WHERE username LIKE ?
        AND dog_name LIKE ?
        AND neighborhood LIKE ?
    """, (
        "%" + username + "%",
        "%" + dog_name + "%",
        "%" + neighborhood + "%"
    )).fetchall()

    print(users)  

    conn.close()

    return render_template(
        "search.html",
        users=users,
        username=username,
        dog_name=dog_name,
        neighborhood=neighborhood
    )

@app.route("/my_profile")
def my_profile():
    user_id = session.get("user_id")

    if user_id is None:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()

    if user_row is None:
        conn.close()
        return "<h2>No profile found.</h2>"

    cursor.execute("SELECT * FROM posts WHERE user_id = ?", (user_id,))
    post_rows = cursor.fetchall()
    conn.close()

    user = {
        "id": user_row["id"],
        "username": user_row["username"],
        "email": user_row["email"],
        "neighborhood": user_row["neighborhood"],
        "dog_name": user_row["dog_name"],
        "dog_breed": user_row["dog_breed"]
    }

    posts = []
    for row in post_rows:
        posts.append({
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "neighborhood": row["neighborhood"],
            "time": row["time"],
            "type": row["type"]
        })

    return render_template("my_profile.html", user=user, posts=posts)

@app.route("/tokens")
def tokens():
    return "<h2>Tokens system (coming soon)</h2>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

init_db()

if __name__ == "__main__":
    app.run(debug=True)

