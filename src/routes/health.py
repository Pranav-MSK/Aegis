# cython: language_level=3
from flask import jsonify, blueprints
from src.config import app, get_app_info

health_bp = blueprints.Blueprint("health", __name__)

# health page
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", 
                    "version": get_app_info().get("version")})


