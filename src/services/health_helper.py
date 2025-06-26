# cython: language_level=3
import os
import sqlite3

EXPAND_USER = os.path.expanduser('~')
DB_PATH = os.path.join(EXPAND_USER, ".database/systemguard.db")

def check_database():
    conn = None  # Initialize conn to None
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Execute a simple query to check the database status
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")        
        cursor.fetchall()  # Fetch the results to ensure the query was executed

        # If no exceptions were raised, the DB is healthy
        db_health = {
            "status": "healthy",
            "version": sqlite3.sqlite_version,
        }
    except sqlite3.Error as e:
        # Handle any exceptions and mark the database as unhealthy
        db_health = {
            "status": "unhealthy",
            "error": str(e),
        }
    finally:
        if conn:  # Only close conn if it was successfully created
            conn.close()  # Ensure the connection is closed

    return db_health