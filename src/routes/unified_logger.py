import os
from datetime import datetime
import json
from flask import Flask, jsonify, render_template, request, Blueprint
from flask_login import login_required
from src.routes.helper.common_helper import admin_required

from src.config import app

unified_logger_bp = Blueprint("unified_logger", __name__)
user_name = os.getenv("USER_NAME")
# Constants
CHUNK_SIZE = 100  # Number of lines to fetch per request

# Load configuration from config file
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "log_directories": [
                {
                    "name": os.path.join(os.path.expanduser('~'), 'logs'),
                    "path": os.path.join(os.path.expanduser('~'), 'logs')
                },
                {
                    "name": "/var/log",
                    "path": "/var/log"
                }
            ]
        }

# Centralized error response
def error_response(message, status_code):
    return jsonify({"error": message}), status_code

@app.route('/unified_logger', methods=['GET'])
@admin_required
def unified_logger():
    return render_template('other/unified_logger.html')

@app.route('/api/v1/logger/directories', methods=['GET'])
@admin_required
def list_directories():
    config = load_config()
    return jsonify(config['log_directories'])

@app.route('/api/v1/logfiles', methods=['GET'])
@admin_required
def list_log_files():
    directory = request.args.get('directory')
    if not directory or not os.path.isdir(directory):
        return error_response("Invalid directory", 400)

    log_files = []
    try:
        for filename in os.listdir(directory):
            log_file_path = os.path.join(directory, filename)
            if filename.endswith('.log') and os.access(log_file_path, os.R_OK):
                stats = os.stat(log_file_path)
                log_files.append({
                    'name': filename,
                    'size': stats.st_size,
                    'modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
                })
        return jsonify(sorted(log_files, key=lambda x: x['modified'], reverse=True)), 200
    except Exception as e:
        return error_response(str(e), 500)

@app.route('/api/v1/logs/<path:filepath>', methods=['GET'])
@admin_required
def get_log_file(filepath):
    file_path = os.path.join('/', filepath)  # Ensure the path is correctly formed
    if not os.path.isfile(file_path):
        return error_response("File not found", 404)

    page = request.args.get('page', 1, type=int)
    chunk_size = request.args.get('chunk_size', CHUNK_SIZE, type=int)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            start_pos = max(0, file_size - (page * chunk_size * 1024))
            f.seek(start_pos)

            if start_pos > 0:
                f.readline()  # Skip partial line

            lines = [f.readline().strip() for _ in range(chunk_size) if f.readline()]

            return jsonify({
                "filename": file_path,
                "content": lines,
                "has_more": start_pos > 0,
                "page": page,
                "total_size": file_size
            }), 200

    except Exception as e:
        return error_response(str(e), 500)

