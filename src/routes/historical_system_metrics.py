# cython: language_level=3
from flask import (
    render_template,
    blueprints,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
)
from flask_login import login_required, current_user

from src.config import app, csrf, get_app_info
from src.routes.helper.common_helper import admin_required
from src.models import ChartConfiguration
from src.logger import get_logger
logger = get_logger(__name__)

graphs_bp = blueprints.Blueprint("graphs", __name__)


@app.route("/system/historical_system_metrics")
@login_required
def historical_system_metrics():
    total_chart = ChartConfiguration.query.filter_by(user_id=current_user.id).count()
    active_chart = ChartConfiguration.query.filter_by(
        user_id=current_user.id, is_active=True
    ).count()
    return render_template("graphs/historical_system_metrics.html", total_chart=total_chart, active_chart=active_chart)

def get_form_value(key, default):
    value = request.form.get(key, default)
    return value if value.strip() else default

@app.route("/chart_configurations", methods=["GET", "POST"])
@login_required
def chart_configurations():
    configs = ChartConfiguration.query.filter_by(user_id=current_user.id).all()
    total_configs = len(configs)

    if request.method == "POST":
        config_id = request.form.get("config_id")

        if config_id:  # Editing an existing configuration
            config = ChartConfiguration.query.get(config_id)
            if config and config.user_id == current_user.id:
                config.metric_name = request.form["metric_name"]
                config.title = request.form["title"]
                config.xlabel = request.form["xlabel"]
                config.ylabel = request.form["ylabel"]
                config.chart_type = request.form.get("chart_type", "line")
                config.tension = get_form_value("tension", 0.4)
                config.point_radius = get_form_value("point_radius", 0)
                config.point_hover_radius = get_form_value("point_hover_radius", 6)
                config.save()
                return redirect(url_for("chart_configurations"))
        else:  # Creating a new configuration
            max_number_of_graphs = get_app_info().get("max_number_of_graphs")
            if max_number_of_graphs is not None and total_configs >= max_number_of_graphs:
                flash(
                    "You have reached the maximum number of graphs allowed for your plan",
                    "danger",
                )
                logger.error(
                    f"User {current_user.username} tried to create a new graph configuration but has reached the maximum number of graphs allowed for their plan"
                )
                return redirect(url_for("chart_configurations"))
            new_config = ChartConfiguration(
                user_id=current_user.id, # type: ignore
                metric_name=request.form["metric_name"], # type: ignore
                title=request.form["title"], # type: ignore
                xlabel=request.form["xlabel"], # type: ignore
                ylabel=request.form["ylabel"], # type: ignore
                chart_type=request.form.get("chart_type", "bar"), # type: ignore
                tension=request.form.get("tension", 0.4), # type: ignore
                point_radius=request.form.get("point_radius", 0), # type: ignore
                point_hover_radius=request.form.get("point_hover_radius", 6), # type: ignore
            )

            new_config.save()
            return redirect(url_for("chart_configurations"))

    return render_template("graphs/chart_configurations.html", configs=configs)


@app.route("/chart_configurations/<int:id>", methods=["DELETE"])
@admin_required
@csrf.exempt
def delete_chart_configuration(id):
    config = ChartConfiguration.query.get(id)
    if config:
        if config.user_id == current_user.id:
            try:
                config.delete()
                return jsonify({"message": "Deleted successfully"}), 200
            except Exception as e:
                return jsonify({"message": "Internal server error"}), 500
        else:
            return jsonify({"message": "Permission denied"}), 403
    else:
        return jsonify({"message": "Configuration not found"}), 404


@app.route("/chart_configurations/<int:id>/activate", methods=["POST"])
@login_required
def activate_chart_configuration(id):
    config = ChartConfiguration.query.get(id)
    if config and config.user_id == current_user.id:
        data = request.get_json()
        is_active = data.get("is_active")
        config.is_active = is_active
        config.save()  # Save the updated status to the database
        return jsonify({"message": "Configuration updated successfully"}), 200
    else:
        return jsonify({"message": "Configuration not found or permission denied"}), 404
