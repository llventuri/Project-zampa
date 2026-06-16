from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import sqlite3
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4 MB max
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY is not set. Add it to your .env file.")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def login_required():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login"))
    return None

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
            dog_breed TEXT,
            dog_sex TEXT,
            dog_age INTEGER,
            dog_weight REAL,
            dog_behaviour TEXT,
            profile_pic TEXT
        )
    """)

    # Migrate existing databases that are missing the new columns
    existing_columns = [row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()]
    new_columns = {
        "dog_sex":       "ALTER TABLE users ADD COLUMN dog_sex TEXT",
        "dog_age":       "ALTER TABLE users ADD COLUMN dog_age INTEGER",
        "dog_weight":    "ALTER TABLE users ADD COLUMN dog_weight REAL",
        "dog_behaviour": "ALTER TABLE users ADD COLUMN dog_behaviour TEXT",
        "profile_pic":   "ALTER TABLE users ADD COLUMN profile_pic TEXT",
    }
    for col, sql in new_columns.items():
        if col not in existing_columns:
            cursor.execute(sql)

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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Migrate existing posts tables missing created_at
    post_cols = [row[1] for row in cursor.execute("PRAGMA table_info(posts)").fetchall()]
    if "created_at" not in post_cols:
        cursor.execute("ALTER TABLE posts ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")

    conn.commit()
    conn.close()

def row_to_user(row):
    """Convert a sqlite3.Row to a plain dict with all user fields."""
    return {
        "id":             row["id"],
        "username":       row["username"],
        "email":          row["email"],
        "neighborhood":   row["neighborhood"],
        "dog_name":       row["dog_name"],
        "dog_breed":      row["dog_breed"],
        "dog_sex":        row["dog_sex"],
        "dog_age":        row["dog_age"],
        "dog_weight":     row["dog_weight"],
        "dog_behaviour":  row["dog_behaviour"],
        "profile_pic":    row["profile_pic"],
    }

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username      = request.form.get("username")
        email         = request.form.get("email")
        password      = request.form.get("password")
        neighborhood  = request.form.get("neighborhood")
        dog_name      = request.form.get("dog_name")
        dog_breed     = request.form.get("dog_breed")
        dog_sex       = request.form.get("dog_sex")
        dog_age       = request.form.get("dog_age") or None
        dog_weight    = request.form.get("dog_weight") or None
        dog_behaviour = request.form.get("dog_behaviour")

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users
                    (username, email, password, neighborhood,
                     dog_name, dog_breed, dog_sex, dog_age, dog_weight, dog_behaviour)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, email, hashed_password, neighborhood,
                  dog_name, dog_breed, dog_sex, dog_age, dog_weight, dog_behaviour))

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
        email    = request.form.get("email")
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
        title       = request.form.get("title")
        description = request.form.get("description")
        neighborhood = request.form.get("neighborhood")
        time        = request.form.get("time")
        post_type   = request.form.get("type")

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

    if selected_neighborhood:
        cursor.execute("""
            SELECT posts.*, users.username
            FROM posts
            JOIN users ON posts.user_id = users.id
            WHERE posts.neighborhood = ?
            ORDER BY posts.created_at DESC
        """, (selected_neighborhood,))
    else:
        cursor.execute("""
            SELECT posts.*, users.username
            FROM posts
            JOIN users ON posts.user_id = users.id
            ORDER BY posts.created_at DESC
        """)

    rows = cursor.fetchall()
    conn.close()

    posts = [{
        "id":           row["id"],
        "title":        row["title"],
        "description":  row["description"],
        "neighborhood": row["neighborhood"],
        "time":         row["time"],
        "type":         row["type"],
        "user_id":      row["user_id"],
        "username":     row["username"],
        "created_at":   row["created_at"],
    } for row in rows]

    return render_template("board.html", posts=posts, selected_neighborhood=selected_neighborhood)

@app.route("/users")
def users_list():
    guard = login_required()
    if guard:
        return guard

    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    users = [row_to_user(row) for row in rows]
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

    user  = row_to_user(user_row)
    posts = [{
        "id":           row["id"],
        "title":        row["title"],
        "description":  row["description"],
        "neighborhood": row["neighborhood"],
        "time":         row["time"],
        "type":         row["type"],
    } for row in post_rows]

    return render_template("user_profile.html", user=user, posts=posts)

@app.route("/community")
def community():
    return "<h2>Community (coming soon)</h2>"

@app.route("/search")
def search():
    guard = login_required()
    if guard:
        return guard

    username     = request.args.get("username", "")
    dog_name     = request.args.get("dog_name", "")
    neighborhood = request.args.get("neighborhood", "")

    conn = get_db_connection()
    rows = conn.execute("""
        SELECT * FROM users
        WHERE username LIKE ?
        AND dog_name LIKE ?
        AND neighborhood LIKE ?
    """, ("%" + username + "%", "%" + dog_name + "%", "%" + neighborhood + "%")).fetchall()
    conn.close()

    users = [row_to_user(row) for row in rows]
    return render_template("search.html", users=users,
                           username=username, dog_name=dog_name, neighborhood=neighborhood)

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

    user  = row_to_user(user_row)
    posts = [{
        "id":           row["id"],
        "title":        row["title"],
        "description":  row["description"],
        "neighborhood": row["neighborhood"],
        "time":         row["time"],
        "type":         row["type"],
    } for row in post_rows]

    return render_template("my_profile.html", user=user, posts=posts)

@app.route("/tokens")
def tokens():
    return "<h2>Tokens system (coming soon)</h2>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/post/delete/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    guard = login_required()
    if guard:
        return guard

    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM posts WHERE id = ? AND user_id = ?", (post_id, user_id))
    post = cursor.fetchone()

    if post is None:
        conn.close()
        return "<h2>Post not found or you don't have permission to delete it.</h2>"

    cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("my_profile"))

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    guard = login_required()
    if guard:
        return guard

    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        neighborhood  = request.form.get("neighborhood")
        dog_name      = request.form.get("dog_name")
        dog_breed     = request.form.get("dog_breed")
        dog_sex       = request.form.get("dog_sex")
        dog_age       = request.form.get("dog_age") or None
        dog_weight    = request.form.get("dog_weight") or None
        dog_behaviour = request.form.get("dog_behaviour")

        # Handle photo upload
        file = request.files.get("profile_pic")
        pic_filename = None
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            pic_filename = secure_filename(f"user_{user_id}.{ext}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], pic_filename))

        if pic_filename:
            cursor.execute("""
                UPDATE users
                SET neighborhood = ?, dog_name = ?, dog_breed = ?,
                    dog_sex = ?, dog_age = ?, dog_weight = ?, dog_behaviour = ?,
                    profile_pic = ?
                WHERE id = ?
            """, (neighborhood, dog_name, dog_breed,
                  dog_sex, dog_age, dog_weight, dog_behaviour, pic_filename, user_id))
        else:
            cursor.execute("""
                UPDATE users
                SET neighborhood = ?, dog_name = ?, dog_breed = ?,
                    dog_sex = ?, dog_age = ?, dog_weight = ?, dog_behaviour = ?
                WHERE id = ?
            """, (neighborhood, dog_name, dog_breed,
                  dog_sex, dog_age, dog_weight, dog_behaviour, user_id))

        conn.commit()
        conn.close()
        return redirect(url_for("my_profile"))

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    conn.close()

    user = row_to_user(user_row)
    return render_template("edit_profile.html", user=user)

init_db()

if __name__ == "__main__":
    app.run(debug=True)
