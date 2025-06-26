# db_connector/sqlite_connector.py

import os
import sqlite3
from typing import List, Tuple, Optional, Union, Dict
import logging

from src.clients.db_client.base import DBConnection, DatabaseError

EXPAND_USER = os.path.expanduser('~')
DEFAULT_SQLITE_PATH = os.path.join(EXPAND_USER, ".database/systemguard.db")

class SQLiteConnection(DBConnection):
    """SQLite implementation of the database connection."""
    
    def __init__(self, db_path: str = DEFAULT_SQLITE_PATH):
        self.db_path = db_path
        self._ensure_directory_exists()
        self.conn: Optional[sqlite3.Connection] = None
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the directory for the database file exists."""
        directory = os.path.dirname(self.db_path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def connect(self) -> bool:
        """Establish a connection to the SQLite database."""
        if self.conn is not None:
            return True
            
        try:
            self.conn = sqlite3.connect(self.db_path)
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")
            return True
        except sqlite3.Error as e:
            return False
    
    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def execute_query(self, query: str, params: Union[Tuple, List, Dict] = ()) -> bool:
        """Execute INSERT, UPDATE, DELETE queries."""
        if not self.conn and not self.connect():
            raise DatabaseError("Could not establish database connection")
            
        try:
            cursor = self.conn.cursor() # type: ignore
            cursor.execute(query, params)
            return True
        except sqlite3.Error as e:
            return False
    
    def fetch_one(self, query: str, params: Union[Tuple, List, Dict] = ()) -> Optional[Tuple]:
        """Fetch a single row."""
        if not self.conn and not self.connect():
            raise DatabaseError("Could not establish database connection")
            
        try:
            cursor = self.conn.cursor() # type: ignore
            cursor.execute(query, params)
            return cursor.fetchone()
        except sqlite3.Error as e:
            return None
    
    def fetch_all(self, query: str, params: Union[Tuple, List, Dict] = ()) -> List[Tuple]:
        """Fetch all matching rows."""
        if not self.conn and not self.connect():
            raise DatabaseError("Could not establish database connection")
            
        try:
            cursor = self.conn.cursor() # type: ignore
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            return []
    
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        if not self.conn and not self.connect():
            raise DatabaseError("Could not establish database connection")
        
        try:
            self.conn.execute("BEGIN TRANSACTION") # type: ignore
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to begin transaction: {e}")
    
    def commit(self) -> None:
        """Commit the current transaction."""
        if not self.conn:
            raise DatabaseError("No active connection to commit")
            
        try:
            self.conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to commit transaction: {e}")
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        if not self.conn:
            raise DatabaseError("No active connection to rollback")
            
        try:
            self.conn.rollback()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to rollback transaction: {e}")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # No exception occurred, commit any pending transaction
            try:
                self.commit()
            except DatabaseError:
                self.rollback()
        else:
            # Exception occurred, rollback any pending transaction
            try:
                self.rollback()
            except DatabaseError:
                pass  # Already in an exception handler, just continue
        self.close()