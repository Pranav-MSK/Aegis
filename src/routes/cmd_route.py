from flask import blueprints
from src.config import app

cmd_bp = blueprints.Blueprint("cmd", __name__)

@app.cli.command("hello")
def hello():
    """Print a hello message."""
    print("Hello, World!")