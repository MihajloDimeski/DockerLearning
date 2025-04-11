from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import psycopg2.extras
import os
import logging
from logging.handlers import RotatingFileHandler
import time

app = Flask(__name__)

# DB config
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "crud_db")
DB_USER = os.getenv("DB_USER", "crud_user")
DB_PASS = os.getenv("DB_PASS", "secret")

# Logging setup
if not os.path.exists('logs'):
    os.makedirs('logs')

log_handler = RotatingFileHandler("logs/app.log", maxBytes=10240, backupCount=5)
log_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)

@app.before_request
def log_request_info():
    app.logger.info(f"{request.remote_addr} - {request.method} {request.path}")

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    conn.autocommit = True
    return conn

# Ensure table exists
CREATE_ITEMS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);
"""

def init_db():
    for attempt in range(10):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(CREATE_ITEMS_TABLE_SQL)
            cur.close()
            conn.close()
            app.logger.info("Items table ensured at startup.")
            return
        except Exception as e:
            app.logger.error(f"DB not ready (attempt {attempt + 1}/10): {e}")
            time.sleep(2)
@app.route('/')
def hub():
    return render_template('hub.html')
@app.route('/app')
def index():
    try:
        app.logger.info("Accessed the home page.")
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM items")
        items = cur.fetchall()
        cur.close()
        conn.close()
        return render_template("index.html", items=items)
    except Exception as e:
        app.logger.error(f"Error loading home page: {e}", exc_info=True)
        return "An error occurred", 500

@app.route('/add', methods=['POST'])
def add():
    try:
        name = request.form['name']
        if name:
            app.logger.info(f"Adding new item: {name}")
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO items (name) VALUES (%s)", (name,))
            cur.close()
            conn.close()
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error adding item: {e}", exc_info=True)
        return "An error occurred", 500

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if request.method == 'POST':
            name = request.form['name']
            app.logger.info(f"Editing item with ID {id}, new name: {name}")
            cur.execute("UPDATE items SET name = %s WHERE id = %s", (name, id))
            cur.close()
            conn.close()
            return redirect(url_for('index'))
        cur.execute("SELECT * FROM items WHERE id = %s", (id,))
        item = cur.fetchone()
        cur.close()
        conn.close()
        return render_template("edit.html", item=item)
    except Exception as e:
        app.logger.error(f"Error editing item ID {id}: {e}", exc_info=True)
        return "An error occurred", 500

@app.route('/delete/<int:id>')
def delete(id):
    try:
        app.logger.info(f"Deleting item with ID {id}")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM items WHERE id = %s", (id,))
        cur.close()
        conn.close()
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error deleting item ID {id}: {e}", exc_info=True)
        return "An error occurred", 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
