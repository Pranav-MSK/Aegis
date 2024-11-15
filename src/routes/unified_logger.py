# cython: language_level=3
import os
from datetime import datetime
from flask import jsonify, render_template, request, Blueprint
from flask_login import login_required

from src.config import app, csrf
from src.models import LogDirectory
from src.routes.helper.access_decorators import systemguard_enterprise

unified_logger_bp = Blueprint("unified_logger", __name__)
CHUNK_SIZE = 100  # Number of lines to fetch per request

# Load configuration from config file
def load_config():
    log_directories = LogDirectory.query.all()
    return {"log_directories": [log_directory.to_dict() for log_directory in log_directories]}

# Centralized error response
def error_response(message, status_code):
    return jsonify({"error": message}), status_code


@app.route("/system/unified_logger", methods=["GET"])
@login_required
@systemguard_enterprise()
def unified_logger():
    return render_template("system/unified_logger.html")


@app.route("/api/v1/logger/directories", methods=["GET", "POST", "DELETE"])
@csrf.exempt
@login_required
@systemguard_enterprise()
def list_directories():
    if request.method == "POST":
        data = request.get_json()
        if not data or "path" not in data:
            return error_response("Invalid request", 400)

        log_directory = LogDirectory.query.filter_by(path=data["path"]).first()
        if log_directory:
            return error_response("Directory already exists", 400)

        new_log_directory = LogDirectory(name=data["path"], path=data["path"])
        new_log_directory.save()
        return jsonify(new_log_directory.to_dict())
    
    if request.method == "DELETE":
        data = request.get_json()
        if not data or "path" not in data:
            return error_response("Invalid request", 400)

        log_directory = LogDirectory.query.filter_by(path=data["path"]).first()
        if not log_directory:
            return error_response("Directory not found", 404)

        log_directory.delete()
        return jsonify({"message": "Directory deleted successfully"})

    config = load_config()
    return jsonify(config["log_directories"])


@app.route("/api/v1/logfiles", methods=["GET"])
@login_required
@systemguard_enterprise()
def list_log_files():
    directory = request.args.get("directory")
    if not directory or not os.path.isdir(directory):
        return error_response("Invalid directory", 400)

    log_files = []
    try:
        for filename in os.listdir(directory):
            log_file_path = os.path.join(directory, filename)
            if filename.endswith(".log") and os.access(log_file_path, os.R_OK):
                stats = os.stat(log_file_path)
                log_files.append(
                    {
                        "name": filename,
                        "size": stats.st_size,
                        "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    }
                )
        return (
            jsonify(sorted(log_files, key=lambda x: x["modified"], reverse=True)),
            200,
        )
    except Exception as e:
        return error_response(str(e), 500)


@app.route("/api/v1/logs/<path:file_path>", methods=["GET"])
@login_required
@systemguard_enterprise()
def get_log_file(file_path):
    file_path = os.path.join("/", file_path)  # Ensure the path is correctly formed
    if not os.path.isfile(file_path):
        return error_response("File not found", 404)

    chunk_size = request.args.get("chunk_size", CHUNK_SIZE, type=int)  # Default chunk size in lines
    stats = os.stat(file_path)

    try:
        # Open the file in binary mode for more precise seeking and decoding
        with open(file_path, "rb") as f:
            # Move to the end of the file
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            lines = []
            buffer = b""
            lines_read = 0

            # Read the file backwards in chunks until enough lines are gathered
            while lines_read < chunk_size and f.tell() > 0:
                # Move the pointer backwards by small chunks
                read_size = min(4096, f.tell())  # Read in chunks of 4KB or less if near start
                f.seek(-read_size, os.SEEK_CUR)
                buffer = f.read(read_size) + buffer  # Prepend new data
                f.seek(-read_size, os.SEEK_CUR)  # Move pointer back to continue

                # Split buffer into lines
                lines = buffer.splitlines()

                # If enough lines collected, stop
                lines_read = len(lines)

            # Get only the last 'chunk_size' lines
            latest_lines = [line.decode("utf-8", errors="ignore") for line in lines[-chunk_size:]]

            return jsonify(
                {
                    "filename": file_path,
                    "content": latest_lines,
                    "has_more": len(lines) > chunk_size,
                    "total_size": file_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                }
            ), 200

    except Exception as e:
        return error_response(str(e), 500)
