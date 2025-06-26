# example_usage.py

# from db_connector import DatabaseFactory
from src.clients.db_client.factory import DatabaseFactory

def sqlite_example():
    """Example of using SQLite connection"""
    print("Running SQLite example...")
    db_path = "/home/alpha/.database/systemguard.db"
    sqlite_db = DatabaseFactory.create_connection('sqlite', db_path=db_path)
    with sqlite_db: #type: ignore
        # Create a table
        sqlite_db.execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE
            )
        """)
        
        # Insert data with transaction
        with sqlite_db.transaction():
            sqlite_db.execute_query(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                ("John Doe", "john@example.com")
            )
        
        # Query data
        result = sqlite_db.fetch_all("SELECT * FROM users")
        print("SQLite results:", result)


if __name__ == "__main__":
    sqlite_example()
    # postgresql_example()