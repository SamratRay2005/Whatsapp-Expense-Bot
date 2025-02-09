import sqlite3
import datetime

DATABASE = 'expenses.db'  # This file will be created in your project directory

def init_db():
    """Connect to the SQLite database and create the 'expenses' table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    create_table_query = """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            amount REAL,
            category TEXT,
            date TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """
    c.execute(create_table_query)
    conn.commit()
    conn.close()

# Initialize the database when the actions server starts
init_db()
