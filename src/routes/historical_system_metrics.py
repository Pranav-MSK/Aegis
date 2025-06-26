from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from src.core.config.app_config import app, csrf
from src.services.common_helper import admin_required
from src.services.chart_config_service import ChartConfigService

graphs_bp = Blueprint("charts", __name__)

@app.route("/system/historical_system_metrics")
@login_required
def historical_system_metrics():
    return ChartConfigService.render_historical_metrics(current_user)

@app.route("/chart_configurations", methods=["GET", "POST"])
@login_required
def chart_configurations():
    if request.method == "POST":
        response = ChartConfigService.create_or_update_chart(current_user, request)
        return response if response else jsonify({"message": "No response from service"}), 400
    response = ChartConfigService.render_chart_config_page(current_user)
    return response if response else jsonify({"message": "No response from service"}), 400

@app.route("/chart_configurations/<int:id>", methods=["DELETE"])
@admin_required
@csrf.exempt
def delete_chart_configuration(id):
    return ChartConfigService.delete_chart(id, current_user)

@app.route("/chart_configurations/<int:id>/activate", methods=["POST"])
@login_required
def activate_chart_configuration(id):
    return ChartConfigService.toggle_chart_activation(id, request, current_user)
