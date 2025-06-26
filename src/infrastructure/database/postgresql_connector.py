# db_connector/postgresql_connector.py

from typing import List, Tuple, Optional, Union, Dict
import logging

from src.infrastructure.database.base import DBConnection, DatabaseError


class PostgreSQLConnection(DBConnection):
    """PostgreSQL implementation of the database connection."""
    
    def __init__(self, host: str, database: str, user: str, password: str, port: int = 5432):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.conn = None
        
        # Import psycopg2 here to avoid making it a hard dependency
        try:
            import psycopg2
            self.psycopg2 = psycopg2
        except ImportError:
            raise ImportError("psycopg2 is required for PostgreSQL support. Install it with 'pip install psycopg2'.")
    
    def connect(self) -> bool:
        """Establish a connection to the PostgreSQL database."""
        if self.conn is not None:
            return True
            
        try:
            self.conn = self.psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )
            return True
        except self.psycopg2.Error as e:
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
        except self.psycopg2.Error as e:
            return False
    
    def fetch_one(self, query: str, params: Union[Tuple, List, Dict] = ()) -> Optional[Tuple]:
        """Fetch a single row."""
        if not self.conn and not self.connect():
            raise DatabaseError("Could not establish database connection")
            
        try:
            cursor = self.conn.cursor() # type: ignore
            cursor.execute(query, params)
            return cursor.fetchone()
        except self.psycopg2.Error as e:
            return None
    
    def fetch_all(self, query: str, params: Union[Tuple, List, Dict] = ()) -> List[Tuple]:
        """Fetch all matching rows."""
        if not self.conn and not self.connect():
            raise DatabaseError("Could not establish database connection")
            
        try:
            cursor = self.conn.cursor() # type: ignore
            cursor.execute(query, params)
            return cursor.fetchall()
        except self.psycopg2.Error as e:
            return []
    
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        if not self.conn and not self.connect():
            raise DatabaseError("Could not establish database connection")
        
        try:
            # PostgreSQL automatically starts a transaction when you execute a command
            # but we can explicitly do it for clarity
            self.conn.autocommit = False # type: ignore
        except self.psycopg2.Error as e:
            raise DatabaseError(f"Failed to begin transaction: {e}")
    
    def commit(self) -> None:
        """Commit the current transaction."""
        if not self.conn:
            raise DatabaseError("No active connection to commit")
            
        try:
            self.conn.commit()
        except self.psycopg2.Error as e:
            raise DatabaseError(f"Failed to commit transaction: {e}")
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        if not self.conn:
            raise DatabaseError("No active connection to rollback")
            
        try:
            self.conn.rollback()
        except self.psycopg2.Error as e:
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