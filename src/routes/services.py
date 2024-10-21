# cython: language_level=3
from flask import render_template, blueprints, jsonify
from http.client import HTTPException

from src.config import app
from src.routes.helper.service_helper import ServiceMonitor

services_bp = blueprints.Blueprint('services', __name__)


@app.get("/api/v1/services")
def get_services():
    """Get all running services."""
    monitor = ServiceMonitor()
    try:
        return jsonify(monitor.get_running_services())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/services/<category>")
def get_services_by_category(category: str):
    """Get services for a specific category."""
    try:
        monitor = ServiceMonitor()
        data = monitor.get_running_services()
        if category not in data['services']:
            raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
        
        return jsonify({
            'timestamp': data['timestamp'],
            'category': category,
            'processes': data['services'][category],
            'summary': data['summary'][category]
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/categories")
def get_categories():
    """Get list of available service categories."""
    monitor = ServiceMonitor()
    return jsonify({
        'categories': list(monitor.service_patterns.keys())
    })


@app.get("/system/services")
def system_services():
    return render_template('other/services.html')