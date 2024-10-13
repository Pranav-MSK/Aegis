# cython: language_level=3
from flask import render_template, blueprints, request, jsonify, redirect, url_for
from flask_login import login_required, current_user

from src.config import app, db, csrf
from src.routes.helper.common_helper import admin_required
from src.models import ChartConfiguration

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

def get_form_value(key, default):
    value = request.form.get(key, default)
    return value if value else default

@app.route('/chart_configurations', methods=['GET', 'POST'])
@login_required
def chart_configurations():
    if request.method == 'POST':
        config_id = request.form.get('config_id')
        
        if config_id:  # Editing an existing configuration
            config = ChartConfiguration.query.get(config_id)
            if config and config.user_id == current_user.id:
                config.metric_name = request.form['metric_name']
                config.label = request.form['label']
                config.title = request.form['title']
                config.xlabel = request.form['xlabel']
                config.ylabel = request.form['ylabel']
                config.tension = request.form.get('tension', 0.4)
                config.point_radius = request.form.get('point_radius', 0)
                config.point_hover_radius = request.form.get('point_hover_radius', 6)
                config.point_border_color = request.form.get('point_border_color', '#fff')
                config.point_hover_background_color = request.form.get('point_hover_background_color', '#fff')
                config.point_hover_border_color = request.form.get('point_hover_border_color', 'rgba(75, 192, 192, 1)')
                
                db.session.commit()
                return redirect(url_for('chart_configurations'))
        else:  # Creating a new configuration
            new_config = ChartConfiguration(
                user_id=current_user.id,
                metric_name=request.form['metric_name'],
                label=request.form['label'],
                title=request.form['title'],
                xlabel=request.form['xlabel'],
                ylabel=request.form['ylabel'],
                tension=request.form.get('tension', 0.4),
                point_radius=request.form.get('point_radius', 0),
                point_hover_radius=request.form.get('point_hover_radius', 6),
                point_border_color=request.form.get('point_border_color', '#fff'),
                point_hover_background_color=request.form.get('point_hover_background_color', '#fff'),
                point_hover_border_color=request.form.get('point_hover_border_color', 'rgba(75, 192, 192, 1)')
            )
            new_config.save()
            return redirect(url_for('chart_configurations'))

    configs = ChartConfiguration.query.filter_by(user_id=current_user.id).all()
    return render_template('graphs/chart_configurations.html', configs=configs)


@app.route('/chart_configurations/<int:id>', methods=['DELETE'])
@login_required
@csrf.exempt
def delete_chart_configuration(id):
    config = ChartConfiguration.query.get(id)
    if config:
        if config.user_id == current_user.id:
            try:
                config.delete()
                return jsonify({'message': 'Deleted successfully'}), 200
            except Exception as e:
                return jsonify({'message': 'Internal server error'}), 500
        else:
            return jsonify({'message': 'Permission denied'}), 403
    else:
        return jsonify({'message': 'Configuration not found'}), 404
