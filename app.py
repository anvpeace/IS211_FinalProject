from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DATABASE = "blog.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def make_slug(title):
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "post"


def unique_slug(title, post_id=None):
    base_slug = make_slug(title)
    slug = base_slug
    counter = 2
    conn = get_db()

    while True:
        if post_id:
            existing = conn.execute(
                "SELECT id FROM posts WHERE slug = ? AND id != ?", (slug, post_id)
            ).fetchone()
        else:
            existing = conn.execute("SELECT id FROM posts WHERE slug = ?", (slug,)).fetchone()

        if existing is None:
            conn.close()
            return slug

        slug = f"{base_slug}-{counter}"
        counter += 1


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            published_date TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            is_published INTEGER NOT NULL DEFAULT 1,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )
    """)

    users = [("peace", "password123"), ("student", "student123")]
    for username, password in users:
        conn.execute(
            "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
            (username, password),
        )

    categories = ["School", "Technology", "Personal"]
    for category in categories:
        conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category,))

    sample = conn.execute("SELECT id FROM posts LIMIT 1").fetchone()
    if sample is None:
        user = conn.execute("SELECT id FROM users WHERE username = ?", ("peace",)).fetchone()
        category = conn.execute("SELECT id FROM categories WHERE name = ?", ("Technology",)).fetchone()
        conn.execute(
            """
            INSERT INTO posts (title, content, published_date, slug, is_published, user_id, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Welcome to My Blog",
                "This is a sample blog post. After logging in, users can add, edit, delete, publish, and unpublish their own posts.",
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                "welcome-to-my-blog",
                1,
                user["id"],
                category["id"],
            ),
        )

    conn.commit()
    conn.close()


def current_user_id():
    return session.get("user_id")


def login_required():
    if "user_id" not in session:
        flash("Please log in first.")
        return False
    return True


@app.route("/")
def index():
    conn = get_db()
    posts = conn.execute(
        """
        SELECT posts.*, users.username, categories.name AS category_name
        FROM posts
        JOIN users ON posts.user_id = users.id
        LEFT JOIN categories ON posts.category_id = categories.id
        WHERE posts.is_published = 1
        ORDER BY posts.published_date DESC
        """
    ).fetchall()
    conn.close()
    return render_template("index.html", posts=posts)


@app.route("/post/<slug>")
def post_detail(slug):
    conn = get_db()
    post = conn.execute(
        """
        SELECT posts.*, users.username, categories.name AS category_name
        FROM posts
        JOIN users ON posts.user_id = users.id
        LEFT JOIN categories ON posts.category_id = categories.id
        WHERE posts.slug = ? AND posts.is_published = 1
        """,
        (slug,),
    ).fetchone()
    conn.close()

    if post is None:
        flash("Post not found.")
        return redirect(url_for("index"))

    return render_template("post_detail.html", post=post)


@app.route("/category/<int:category_id>/<category_name>")
def posts_by_category(category_id, category_name):
    conn = get_db()
    posts = conn.execute(
        """
        SELECT posts.*, users.username, categories.name AS category_name
        FROM posts
        JOIN users ON posts.user_id = users.id
        LEFT JOIN categories ON posts.category_id = categories.id
        WHERE posts.is_published = 1 AND posts.category_id = ?
        ORDER BY posts.published_date DESC
        """,
        (category_id,),
    ).fetchall()
    conn.close()
    return render_template("index.html", posts=posts, category_filter=category_name)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("You are now logged in.")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    posts = conn.execute(
        """
        SELECT posts.*, categories.name AS category_name
        FROM posts
        LEFT JOIN categories ON posts.category_id = categories.id
        WHERE posts.user_id = ?
        ORDER BY posts.published_date DESC
        """,
        (current_user_id(),),
    ).fetchall()
    conn.close()
    return render_template("dashboard.html", posts=posts)


@app.route("/add", methods=["GET", "POST"])
def add_post():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        category_id = request.form.get("category_id") or None
        is_published = 1 if request.form.get("is_published") else 0
        slug = unique_slug(title)
        published_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn.execute(
            """
            INSERT INTO posts (title, content, published_date, slug, is_published, user_id, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (title, content, published_date, slug, is_published, current_user_id(), category_id),
        )
        conn.commit()
        conn.close()
        flash("Post added successfully.")
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("post_form.html", categories=categories, post=None, action="Add")


@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    post = conn.execute(
        "SELECT * FROM posts WHERE id = ? AND user_id = ?",
        (post_id, current_user_id()),
    ).fetchone()
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()

    if post is None:
        conn.close()
        flash("Post not found.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        category_id = request.form.get("category_id") or None
        is_published = 1 if request.form.get("is_published") else 0
        slug = unique_slug(title, post_id)

        conn.execute(
            """
            UPDATE posts
            SET title = ?, content = ?, category_id = ?, is_published = ?, slug = ?
            WHERE id = ? AND user_id = ?
            """,
            (title, content, category_id, is_published, slug, post_id, current_user_id()),
        )
        conn.commit()
        conn.close()
        flash("Post updated successfully.")
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("post_form.html", categories=categories, post=post, action="Edit")


@app.route("/delete/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute(
        "DELETE FROM posts WHERE id = ? AND user_id = ?",
        (post_id, current_user_id()),
    )
    conn.commit()
    conn.close()
    flash("Post deleted.")
    return redirect(url_for("dashboard"))


@app.route("/toggle/<int:post_id>", methods=["POST"])
def toggle_publish(post_id):
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    post = conn.execute(
        "SELECT is_published FROM posts WHERE id = ? AND user_id = ?",
        (post_id, current_user_id()),
    ).fetchone()

    if post:
        new_status = 0 if post["is_published"] else 1
        conn.execute(
            "UPDATE posts SET is_published = ? WHERE id = ? AND user_id = ?",
            (new_status, post_id, current_user_id()),
        )
        conn.commit()
        flash("Post status updated.")

    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/categories", methods=["GET", "POST"])
def categories():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":
        name = request.form["name"].strip()
        if name:
            conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
            conn.commit()
            flash("Category saved.")

    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return render_template("category_form.html", categories=categories)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
