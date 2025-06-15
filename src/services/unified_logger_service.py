import os
from datetime import datetime
from flask import jsonify
from src.models import LogDirectory


class UnifiedLoggerService:
    def __init__(self, chunk_size: int = 100):
        self.chunk_size = chunk_size

    def _error_response(self, message, status_code):
        return jsonify({"error": message}), status_code

    def fetch_log_directories(self):
        directories = LogDirectory.query.all()
        return jsonify([d.to_dict() for d in directories]), 200

    def add_log_directory(self, data):
        if not data or "path" not in data:
            return self._error_response("Invalid request", 400)

        if LogDirectory.query.filter_by(path=data["path"]).first():
            return self._error_response("Directory already exists", 400)

        log_dir = LogDirectory(name=data["path"], path=data["path"])
        log_dir.save()
        return jsonify(log_dir.to_dict()), 201

    def delete_log_directory(self, data):
        if not data or "path" not in data:
            return self._error_response("Invalid request", 400)

        log_dir = LogDirectory.query.filter_by(path=data["path"]).first()
        if not log_dir:
            return self._error_response("Directory not found", 404)

        log_dir.delete()
        return jsonify({"message": "Directory deleted successfully"}), 200

    def get_log_files_in_directory(self, directory: str):
        if not directory or not os.path.isdir(directory):
            return self._error_response("Invalid directory", 400)

        log_files = []
        try:
            for filename in os.listdir(directory):
                full_path = os.path.join(directory, filename)
                if filename.endswith(".log") and os.access(full_path, os.R_OK):
                    stats = os.stat(full_path)
                    log_files.append({
                        "name": filename,
                        "size": stats.st_size,
                        "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
                    })

            sorted_files = sorted(log_files, key=lambda x: x["modified"], reverse=True)
            return jsonify(sorted_files), 200
        except Exception as e:
            return self._error_response(str(e), 500)

    def tail_log_file(self, file_path: str, chunk_size):
        file_path = os.path.join("/", file_path)

        if not os.path.isfile(file_path):
            return self._error_response("File not found", 404)

        chunk_size = chunk_size or self.chunk_size

        try:
            with open(file_path, "rb") as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                lines = []
                buffer = b""
                lines_read = 0

                while lines_read < chunk_size and f.tell() > 0:
                    read_size = min(4096, f.tell())
                    f.seek(-read_size, os.SEEK_CUR)
                    buffer = f.read(read_size) + buffer
                    f.seek(-read_size, os.SEEK_CUR)
                    lines = buffer.splitlines()
                    lines_read = len(lines)

                latest_lines = [line.decode("utf-8", errors="ignore") for line in lines[-chunk_size:]]
                stats = os.stat(file_path)

                return jsonify({
                    "filename": file_path,
                    "content": latest_lines,
                    "has_more": len(lines) > chunk_size,
                    "total_size": file_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
                }), 200

        except Exception as e:
            return self._error_response(str(e), 500)
