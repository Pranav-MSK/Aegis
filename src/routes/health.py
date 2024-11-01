# cython: language_level=3
import time
from flask import jsonify, blueprints
from src.config import app, get_app_info

health_bp = blueprints.Blueprint("health", __name__)

# health page
@app.route("/health", methods=["GET"])
def health():
    start = time.time()
    end = time.time()
    ping_ms = round((end - start) * 1000, 2)
    return jsonify(
        {
            "status": "ok",
            "version": get_app_info().get("version"),
            "ping": ping_ms
        }
    )
