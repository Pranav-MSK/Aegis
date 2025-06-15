# cython: language_level=3
from flask import render_template, request, Blueprint
from flask_login import login_required

from src.config.app_config import app, csrf
from src.services.unified_logger_service import UnifiedLoggerService
from src.services.decorators.access_decorators import systemguard_enterprise

unified_logger_bp = Blueprint("unified_logger", __name__)
logger_service = UnifiedLoggerService()


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
        return logger_service.add_log_directory(request.get_json())
    elif request.method == "DELETE":
        return logger_service.delete_log_directory(request.get_json())
    return logger_service.fetch_log_directories()


@app.route("/api/v1/logfiles", methods=["GET"])
@login_required
@systemguard_enterprise()
def list_log_files():
    directory = request.args.get("directory")
    if directory is None:
        return {"error": "Directory parameter is required"}, 400
    return logger_service.get_log_files_in_directory(directory)


@app.route("/api/v1/logs/<path:file_path>", methods=["GET"])
@login_required
@systemguard_enterprise()
def get_log_file(file_path):
    chunk_size = request.args.get("chunk_size", 100, type=int)
    return logger_service.tail_log_file(file_path, chunk_size)
