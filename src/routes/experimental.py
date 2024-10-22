# cython: language_level=3
from flask import Blueprint

from src.config import app
experimental_bp = Blueprint('experimental', __name__)


@app.route('/experimental', methods=['GET', 'POST'])
def experimental():
    """
    Flask view for the experimental page. Handles both GET and POST requests:
    - GET: Displays the experimental page.
    - POST: Handles form data.
    """
    return "Experimental page"