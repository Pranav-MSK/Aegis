# cython: language_level=3
from flask import blueprints
from src.core.config.app_config import app

cmd_bp = blueprints.Blueprint("cmd", __name__)

@app.cli.command("hello")
def hello():
    """Print a hello message."""
    print("Hello, World!")

# write some flask cli helpful command

@app.cli.command("create_user")
def create_user():
    """Create a new user."""
    print("User created successfully.")

@app.cli.command("delete_user")
def delete_user():
    """Delete a user."""
    print("User deleted successfully.")

@app.cli.command("update_user")
def update_user():
    """Update a user."""
    print("User updated successfully.")

@app.cli.command("list_users")
def list_users():
    """List all users."""
    print("List of users.")