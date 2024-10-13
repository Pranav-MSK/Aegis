# cython: language_level=3
from flask import render_template, blueprints, request, jsonify
from src.config import app
from src.routes.helper.common_helper import admin_required

graphs_bp = blueprints.Blueprint("graphs", __name__)

@app.route('/historical_system_metrics')
@admin_required
def historical_system_metrics():
    return render_template('graphs/historical_system_metrics.html')


@app.route('/historical_alerts_metrics')
@admin_required
def historical_alerts_metrics():
    return render_template('graphs/historical_alerts_metrics.html')


@app.route('/experimental_system_metrics')
@admin_required
def historical_system_metrics_():
    return render_template('graphs/experimental_system_metrics.html')
