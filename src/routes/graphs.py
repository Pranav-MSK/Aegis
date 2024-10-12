# cython: language_level=3
from flask import render_template, blueprints, request, jsonify
from src.config import app
from src.routes.helper.common_helper import admin_required
from src.models import GraphConfigs

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


@app.route('/graph_config', methods=['GET', 'POST'])
@admin_required
def graph_config():
    if request.method == 'GET':
        graph_configs = GraphConfigs.query.all()
        return render_template('graphs/graph_config.html', graph_configs=graph_configs)
    if request.method == 'POST':
        data = request.json
        graph = GraphConfigs(
            title=data['title'],
            metrics_key=data['metrics_key'],
            type=data['type'],
            y_label=data['y_label'],
            x_label=data['x_label'],
            description=data['description'],
            color_scheme=data['color_scheme'],
            data_source=data['data_source'],
            refresh_interval=data['refresh_interval'],
            display_options=data['display_options']
        )
        graph.save()
        return jsonify({'message': 'Graph config added successfully'}), 200
    return jsonify({'message': 'Invalid request'}), 400