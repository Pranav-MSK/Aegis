# db_connector/factory.py

import os
from src.clients.db_client.base import DBConnection
from src.clients.db_client.sqlite_connector import SQLiteConnection, DEFAULT_SQLITE_PATH
from src.clients.db_client.postgresql_connector import PostgreSQLConnection

class DatabaseFactory:
    """Factory class for creating database connections."""
    
    @staticmethod
    def create_connection(db_type: str, **kwargs) -> DBConnection:
        """
        Create and return a database connection based on the specified type.
        
        Args:
            db_type: The type of database ('sqlite' or 'postgresql')
            **kwargs: Additional parameters specific to the database type
                
                For SQLite:
                    - db_path: Path to the SQLite database file
                
                For PostgreSQL:
                    - host: Database server host
                    - database: Database name
                    - user: Username
                    - password: Password
                    - port: Port number (default: 5432)
                    
        Returns:
            A database connection instance
        """
        print("Kwargs received:", kwargs)  # Debugging line to check received parameters
        if db_type.lower() == 'sqlite':
            db_path = kwargs.get('db_path', DEFAULT_SQLITE_PATH)
            return SQLiteConnection(db_path)
        elif db_type.lower() == 'postgresql':
            required_params = ['host', 'database', 'user', 'password']
            for param in required_params:
                if param not in kwargs:
                    raise ValueError(f"Missing required parameter '{param}' for PostgreSQL connection")
            
            return PostgreSQLConnection(
                host=kwargs['host'],
                database=kwargs['database'],
                user=kwargs['user'],
                password=kwargs['password'],
                port=kwargs.get('port', 5432)
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")