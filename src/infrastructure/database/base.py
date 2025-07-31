# cython: language_level=3
# db_connector/base.py

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Union, Dict
from contextlib import contextmanager


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass

class DBConnection(ABC):
    """Abstract base class for database connections."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish a connection to the database."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Union[Tuple, List, Dict] = ()) -> bool:
        """Execute INSERT, UPDATE, DELETE queries."""
        pass
    
    @abstractmethod
    def fetch_one(self, query: str, params: Union[Tuple, List, Dict] = ()) -> Optional[Tuple]:
        """Fetch a single row."""
        pass
    
    @abstractmethod
    def fetch_all(self, query: str, params: Union[Tuple, List, Dict] = ()) -> List[Tuple]:
        """Fetch all matching rows."""
        pass
    
    @abstractmethod
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
    
    @contextmanager
    def transaction(self):
        """Context manager for handling transactions."""
        try:
            self.begin_transaction()
            yield
            self.commit()
        except Exception as e:
            self.rollback()
            raise DatabaseError(f"Transaction failed: {e}")