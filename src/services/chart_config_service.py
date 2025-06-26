from flask import render_template, redirect, url_for, jsonify, flash
from src.models import ChartConfiguration
from src.helper.request_utils import get_form_value
from src.core.config.app_config import get_app_info
from src.helper.logger import get_logger

logger = get_logger(__name__)

class ChartConfigService:

    @staticmethod
    def render_historical_metrics(user):
        total = ChartConfiguration.query.filter_by(user_id=user.id).count()
        active = ChartConfiguration.query.filter_by(user_id=user.id, is_active=True).count()
        return render_template("graphs/historical_system_metrics.html", total_chart=total, active_chart=active)

    @staticmethod
    def render_chart_config_page(user):
        configs = ChartConfiguration.query.filter_by(user_id=user.id).all()
        return render_template("graphs/chart_configurations.html", configs=configs)

    @staticmethod
    def create_or_update_chart(user, request):
        configs = ChartConfiguration.query.filter_by(user_id=user.id).all()
        config_id = request.form.get("config_id")

        if config_id:
            return ChartConfigService._update_existing_config(config_id, user, request)

        if ChartConfigService._reached_limit(user, configs):
            return redirect(url_for("chart_configurations"))

        ChartConfigService._create_new_config(user, request)
        return redirect(url_for("chart_configurations"))

    @staticmethod
    def _update_existing_config(config_id, user, request):
        config = ChartConfiguration.query.get(config_id)
        if config and config.user_id == user.id:
            config.metric_name = request.form["metric_name"]
            config.title = request.form["title"]
            config.xlabel = request.form["xlabel"]
            config.ylabel = request.form["ylabel"]
            config.chart_type = request.form.get("chart_type", "line")
            config.tension = get_form_value("tension", 0.4)
            config.point_radius = get_form_value("point_radius", 0)
            config.point_hover_radius = get_form_value("point_hover_radius", 6)
            config.save()

    @staticmethod
    def _reached_limit(user, configs):
        max_graphs = get_app_info().get("max_number_of_graphs")
        if max_graphs is not None and len(configs) >= max_graphs:
            flash("You have reached the maximum number of graphs allowed for your plan", "danger")
            logger.error(f"User {user.username} exceeded max graph limit")
            return True
        return False

    @staticmethod
    def _create_new_config(user, request):
        new_config = ChartConfiguration(
            user_id=user.id, #type: ignore
            metric_name=request.form["metric_name"], #type: ignore
            title=request.form["title"], #type: ignore
            xlabel=request.form["xlabel"], #type: ignore
            ylabel=request.form["ylabel"], #type: ignore
            chart_type=request.form.get("chart_type", "bar"), #type: ignore
            tension=request.form.get("tension", 0.4), #type: ignore
            point_radius=request.form.get("point_radius", 0), #type: ignore
            point_hover_radius=request.form.get("point_hover_radius", 6), #type: ignore
        )
        new_config.save()

    @staticmethod
    def delete_chart(chart_id, user):
        config = ChartConfiguration.query.get(chart_id)
        if not config:
            return jsonify({"message": "Configuration not found"}), 404

        if config.user_id != user.id:
            return jsonify({"message": "Permission denied"}), 403

        try:
            config.delete()
            return jsonify({"message": "Deleted successfully"}), 200
        except Exception:
            return jsonify({"message": "Internal server error"}), 500

    @staticmethod
    def toggle_chart_activation(chart_id, request, user):
        config = ChartConfiguration.query.get(chart_id)
        if config and config.user_id == user.id:
            data = request.get_json()
            config.is_active = data.get("is_active", True)
            config.save()
            return jsonify({"message": "Configuration updated successfully"}), 200
        return jsonify({"message": "Configuration not found or permission denied"}), 404
