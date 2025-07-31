# cython: language_level=3
from flask import Blueprint, jsonify

from src.core.config.app_config import app
from src.services.common_helper import admin_required
from src.services.ec2_metadata_service import Ec2MetadataService

ec2_metadata_bp = Blueprint("experimental", __name__)

@app.route("/api/v1/ec2_metadata", methods=["GET"])
@admin_required
def ec2_metadata():
    instance_data = Ec2MetadataService.handle_instance_metadata()
    return jsonify(instance_data)
