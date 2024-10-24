# cython: language_level=3
from flask import render_template, blueprints, jsonify
from http.client import HTTPException

from src.config import app
from src.routes.helper.service_helper import ServiceMonitor

services_bp = blueprints.Blueprint('services', __name__)


@app.get("/api/v1/services")
def fetch_all_running_services():
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
            'summary': data['summary'][category],
            'count': len(data['services'][category])
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/services/categories")
def list_service_categories():
    """Get list of available service categories."""
    monitor = ServiceMonitor()
    return jsonify({
        'categories': list(monitor.service_patterns.keys()),
        'count': len(monitor.service_patterns),
    })


@app.get("/system/services")
def show_system_services():
    return render_template('other/services.html')

