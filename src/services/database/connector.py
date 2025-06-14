# cython: language_level=3
import os
import sqlite3
from typing import List, Tuple, Optional, Union

EXPAND_USER = os.path.expanduser('~')
DB_PATH = os.path.join(EXPAND_USER, ".database/systemguard.db")

class DatabaseConnector:
    """A class to handle SQLite database connections and operations."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> bool:
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
            self.conn = None

    def execute_query(self, query: str, params: Union[Tuple, List] = ()) -> bool:
        """Execute INSERT, UPDATE, DELETE queries."""
        if not self.conn:
            self.connect()
        try:
            if self.conn is None:
                raise sqlite3.Error("Database connection is not established.")
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Query execution error: {e}")
            return False

    def fetch_one(self, query: str, params: Union[Tuple, List] = ()) -> Optional[Tuple]:
        """Fetch a single row."""
        if not self.conn:
            self.connect()
        try:
            if self.conn is None:
                raise sqlite3.Error("Database connection is not established.")
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Fetch error: {e}")
            return None

    def fetch_all(self, query: str, params: Union[Tuple, List] = ()) -> List[Tuple]:
        """Fetch all matching rows."""
        if not self.conn:
            self.connect()
        try:
            if self.conn is None:
                raise sqlite3.Error("Database connection is not established.")
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Fetch all error: {e}")
            return []

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
