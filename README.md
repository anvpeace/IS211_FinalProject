# IS211_FinalProject

The app allows a user to view published blog posts, log in, manage their own posts from a dashboard, add new posts, edit posts, delete posts, and publish or unpublish posts. The homepage shows only published posts in reverse chronological order, with the newest posts first.

I chose the blog application option because it meets the main project requirements while keeping the design simple and clear. The project uses Flask for the web application and SQLite for the database. The app uses multiple HTML templates and a basic CSS file so the project is organized and easier to understand.

## Extra Credit Features Included

This project includes multiple extra credit features:

1. Multiple users are supported through a users table in the database.
2. Each post has a permalink using a slug created from the post title.
3. Users can unpublish and publish their posts without deleting them.
4. Posts can be assigned to categories, and category links show only posts in that category.

## Database Model

The database has three tables: users, posts, and categories.

The users table stores the username and password for each login account. The posts table stores the title, content, published date, slug, published status, the user who wrote the post, and the category connected to the post. The categories table stores category names. A post belongs to one user, and a post can also belong to one category.

The passwords are stored as plain text because the assignment says password encryption is not required for this project. In a real application, passwords should always be encrypted or hashed.

## How to Run the Project

1. Install Flask:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
python app.py
```

3. Open the app in a browser:

**The URL can be found in terminal after running program.**

**The database will be created automatically when the app is first run.**

## Test Login Accounts

Username: student  
Password: student123

## Project Files

- app.py: Main Flask application and database logic
- blog.db: SQLite database file created automatically after running the app
- templates/: HTML files used by Flask
- static/style.css: Basic styling
- requirements.txt: Flask dependency
- README.md: Project explanation and setup instructions