from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Temporary storage (replace later with database)
users = []
posts = []
current_user_id = 1

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

        # Store it (temporary)
        user = {
            "id": len(users) + 1,
            "username": username,
            "email": email,
            "neighborhood": neighborhood,
            "dog": {
                "name": dog_name,
                "breed": dog_breed
            }
        }

        users.append(user)

        return redirect(url_for("success"))

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

        post = {
            "title": title,
            "description": description,
            "neighborhood": neighborhood,
            "time": time,
            "type": post_type,
            "user_id": current_user_id
        }

        posts.append(post)

    # Filtering
    selected_neighborhood = request.args.get("neighborhood")

    if selected_neighborhood and selected_neighborhood != "":
        filtered_posts = [
            post for post in posts
            if post["neighborhood"] == selected_neighborhood
        ]
    else:
        filtered_posts = posts

    for post in filtered_posts:
        user = next((u for u in users if u["id"] == post["user_id"]), None)
        post["username"] = user["username"] if user else "Unknown"

    return render_template(
        "board.html",
        posts=filtered_posts,
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

if __name__ == "__main__":
    app.run(debug=True)
