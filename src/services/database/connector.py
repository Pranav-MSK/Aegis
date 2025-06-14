# cython: language_level=3
import os
import sqlite3

EXPAND_USER = os.path.expanduser('~')
DB_PATH = os.path.join(EXPAND_USER, ".database/systemguard.db")

class DatabaseConnector:
    """A class to handle database connections and operations."""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Establish a connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            return True
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return False

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
