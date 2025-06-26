# cython: language_level=3
import requests
import asyncio
import aiohttp
from datetime import datetime, timezone
from flask import jsonify, blueprints, request, render_template
from flask_login import login_required, current_user
from src.config.app_config import app, db, csrf
from src.models import (
    UserDashboardSettings,
    AlertTicket,
    ChartConfiguration,
    UserProfile,
)
from src.helper.system_metrics import _collect_metrics
from src.helper.os_info import (
    get_os_release_info,
    get_os_info,
)
from src.helper.cache_utils import get_cached_value

from src.services.common_helper import admin_required
from src.services.prometheus_helper import (
    load_prometheus_config,
    save_prometheus_config,
    load_alert_rules,
    save_alert_rules,
)
from src.config.app_config import disk_metrics, network_metrics
from src.services.health_helper import check_database
from src.config.config_loader import configuration_settings
from src.helper.logger import get_logger
from src.clients.http_client.client import HttpClient

# Initialize logger
logger = get_logger(__name__)

prometheus_api_client = HttpClient("prometheus")
alertmanager_api_client = HttpClient("alertmanager")
api_bp = blueprints.Blueprint("api", __name__)

cache = {}

PROMETHEUS_BASE_URL = configuration_settings.get("monitoring.prometheus", "BASE_URL")
QUERY_API_URL = configuration_settings.get("monitoring.prometheus", "QUERY_API")
TARGETS_API_URL = configuration_settings.get("monitoring.prometheus", "TARGETS_API")


@app.route("/api/v1/system/metrics", methods=["GET"])
@csrf.exempt
@login_required
def system_api():
    try:
        system_info = _collect_metrics()
        return jsonify(system_info), 200
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "An error occurred while fetching the system information",
                    "details": str(e),
                }
            ),
            500,
        )


async def fetch_metric(session, metric_query, start_time, end_time, step):
    params = {"query": metric_query, "start": start_time, "end": end_time, "step": step}
    async with session.get(QUERY_API_URL, params=params) as response:
        return await response.json()


async def fetch_all_metrics(metrics, start_time, end_time, step):
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_metric(session, query, start_time, end_time, step)
            for query in metrics
        ]
        results = await asyncio.gather(*tasks)
        return results


def get_cached_data(cache_key):
    return cache.get(cache_key)


def set_cached_data(cache_key, data, timeout=60):
    cache[cache_key] = data


@app.route("/api/v1/prometheus/graphs_data", methods=["GET"])
@login_required
def graph_data_api():
    try:
        PROMETHEUS_METRICS = (
            ChartConfiguration.query.with_entities(ChartConfiguration.metric_name)
            .filter_by(user_id=current_user.id, is_active=True)
            .all()
        )
        PROMETHEUS_METRICS = [metric.metric_name for metric in PROMETHEUS_METRICS]
        # Initialize lists for the data
        time_data = []
        metric_data = {}
        current_time = datetime.now()

        # Get the time filter from query parameters
        time_filter = request.args.get("filter", default="1 day")

        # Determine the start time based on the filter
        time_deltas = {
            "1 minute": 1 * 60,
            "5 minutes": 5 * 60,
            "15 minutes": 15 * 60,
            "30 minutes": 30 * 60,
            "1 hour": 60 * 60,
            "3 hours": 3 * 60 * 60,
            "6 hours": 6 * 60 * 60,
            "12 hours": 12 * 60 * 60,
            "1 day": 24 * 60 * 60,
            "2 days": 2 * 24 * 60 * 60,
            "3 days": 3 * 24 * 60 * 60,
            "15 days": 15 * 24 * 60 * 60,
            "1 week": 7 * 24 * 60 * 60,
            "1 month": 30 * 24 * 60 * 60,
            "3 months": 90 * 24 * 60 * 60,
        }

        # Get the time range in seconds
        time_range_seconds = time_deltas.get(time_filter, 24 * 60 * 60)

        # Prepare time parameters for the Prometheus query
        end_time = int(current_time.timestamp())
        start_time = end_time - time_range_seconds

        step = "30m"
        # Determine the step based on the time range
        if time_range_seconds <= 60:  # 15 minutes
            step = "2s"
        elif time_range_seconds <= 900:  # 15 minutes
            step = "10s"
        elif time_range_seconds <= 3600:  # 1 hour
            step = "15s"
        elif time_range_seconds <= 86400:  # 1 day
            step = "20s"
        elif time_range_seconds <= 259200:  # 3 days
            step = "5m"
        elif time_range_seconds <= 604800:  # 1 week
            step = "30m"

        # Cache key generation
        cache_key = f"{time_filter}_{start_time}_{end_time}_{step}"
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return jsonify(cached_data), 200

        # Fetch all metrics asynchronously
        results = asyncio.run(
            fetch_all_metrics(PROMETHEUS_METRICS, start_time, end_time, step)
        )

        # Process the results and populate time_data and metric_data
        for idx, metric in enumerate(PROMETHEUS_METRICS):
            result = results[idx].get("data", {}).get("result", [])
            if result:
                metric_data[metric] = []
                for series in result:
                    series_data = {"metric": series.get("metric"), "values": {}}
                    for value in series.get("values", []):
                        timestamp = datetime.fromtimestamp(
                            float(value[0]), tz=timezone.utc
                        ).isoformat()
                        if timestamp not in time_data:
                            time_data.append(timestamp)
                        series_data["values"][timestamp] = value[1]
                    metric_data[metric].append(series_data)

        # Sort the time data for proper alignment
        time_data.sort()

        # Align data for each metric
        for metric, series_list in metric_data.items():
            for series in series_list:
                aligned_values = [
                    series["values"].get(timestamp, None) for timestamp in time_data
                ]
                series["values"] = aligned_values

        # Prepare the final response
        response_data = {
            "time": time_data,
            **{
                metric: [
                    {"metric": s["metric"], "values": s["values"]} for s in series_list
                ]
                for metric, series_list in metric_data.items()
            },
            "current_time": current_time,
        }

        # Cache the response
        set_cached_data(cache_key, response_data)

        # Return the data as JSON
        return jsonify(response_data), 200

    except Exception as e:
        # Handle and log the error for debugging purposes
        logger.error(f"Error fetching graph data: {str(e)}")
        return (
            jsonify(
                {
                    "error": "An error occurred while fetching the graph data",
                    "details": str(e),
                }
            ),
            500,
        )


@app.route("/api/v1/targets", methods=["GET"])
@admin_required
def get_prometheus_targets():
    try:
        # Query Prometheus API to get the targets
        response = prometheus_api_client.get("/api/v1/targets")

        # Check if the request was successful
        if response.status_code == 200:
            targets_data = response.json().get("data", {})
            active_targets = targets_data.get("activeTargets", [])
            dropped_targets = targets_data.get("droppedTargets", [])

            # Return the active and dropped targets as JSON
            return (
                jsonify(
                    {
                        "active_targets": active_targets,
                        "dropped_targets": dropped_targets,
                    }
                ),
                200,
            )
        else:
            # Handle non-200 responses from Prometheus
            return (
                jsonify(
                    {
                        "error": "Failed to fetch targets from Prometheus",
                        "details": response.text,
                    }
                ),
                response.status_code,
            )

    except Exception as e:
        # Handle exceptions
        return (
            jsonify(
                {
                    "error": "An error occurred while fetching Prometheus targets",
                    "details": str(e),
                }
            ),
            500,
        )


@app.route("/api/v1/refresh-interval", methods=["GET", "POST"])
@login_required
def manage_refresh_interval():
    try:
        if request.method == "GET":
            settings = UserDashboardSettings.query.filter_by(
                user_id=current_user.id
            ).first()
            if not settings:
                return jsonify({"refresh_interval": 30}), 200  # Default to 30 seconds
            return (
                jsonify(
                    {
                        "success": "Refresh interval fetched successfully",
                        "refresh_interval": settings.refresh_interval,
                    }
                ),
                200,
            )

        # Update refresh interval (POST request)
        if request.method == "POST":
            
            if not request.is_json or request.json is None:
                return jsonify({"error": "Invalid or missing JSON in request"}), 400
        
            new_interval = request.json.get("refresh_interval")

            # Validate the new refresh interval
            if not isinstance(new_interval, int) or new_interval <= 0:
                return jsonify({"error": "Invalid refresh interval value"}), 400

            # Find or create the user settings
            settings = UserDashboardSettings.query.filter_by(
                user_id=current_user.id
            ).first()
            if not settings:
                settings = UserDashboardSettings(
                    user_id=current_user.id, refresh_interval=new_interval # type: ignore
                )
                db.session.add(settings)
            else:
                settings.refresh_interval = new_interval

            settings.save()
            return (
                jsonify(
                    {
                        "success": "Refresh interval updated successfully",
                        "refresh_interval": new_interval,
                    }
                ),
                200,
            )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

    return {
        "error": "Method not allowed. Use GET to fetch or POST to update the refresh interval."
    }, 405


@app.route("/api/v1/os-info", methods=["GET"])
@login_required
def get_os_info_api():
    os_info = get_cached_value("os_info", get_os_info)
    try:
        os_info.update(get_cached_value("os_release_info", get_os_release_info))
        return jsonify(os_info), 200
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "An error occurred while fetching the OS information",
                    "details": str(e),
                }
            ),
            500,
        )


# Endpoint to view the current configuration
@app.route("/api/v1/prometheus/config", methods=["GET", "POST"])
def manage_prometheus_config():
    config = load_prometheus_config()
    if request.method == "POST":
        new_config = request.json
        config.update(new_config) # type: ignore
        save_prometheus_config(config)
        return jsonify({"message": "Configuration updated successfully"}), 200
    return jsonify(config)


# Endpoint to get the current alert rules
@app.route("/api/v1/prometheus/rules", methods=["GET", "POST"])
def manage_alert_rules():
    if request.method == "POST":
        new_rule = request.json
        rules = load_alert_rules()
        if "groups" not in rules:
            rules["groups"] = []
        rules["groups"].append(new_rule)
        save_alert_rules(rules)
        return jsonify({"message": "Alert rule added successfully"}), 200

    rules = load_alert_rules()
    return jsonify(rules)

@app.route("/api/v1/prometheus/ready")
def ready_prometheus():
    response = prometheus_api_client.get("/-/ready", timeout=5)

    if response.status_code == 200:
        return jsonify({"status": "success", "message": response.text}), 200
    else:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Prometheus is not ready.",
                    "details": response.text,
                }
            ),
            response.status_code,
        )

# Route to get the current retention time
@app.route("/api/v1/get-retention", methods=["GET"])
def get_retention():
    try:
        # Fetch current flags from Prometheus
        response = prometheus_api_client.get("/api/v1/status/flags")
        flags = response.json().get("data", {})

        # Get the current value of "storage.tsdb.retention.time"
        retention_time = flags.get("storage.tsdb.retention.time", "unknown")
        if retention_time == "0s":
            retention_time = "Forever"

        return jsonify({"retention_time": retention_time}), 200

    except requests.RequestException as e:
        return (
            jsonify(
                {
                    "error": "Failed to fetch retention time from Prometheus",
                    "details": str(e),
                }
            ),
            500,
        )
    except Exception as e:
        return (
            jsonify({"error": "Failed to retrieve retention time", "details": str(e)}),
            500,
        )


# alert history api
@app.route("/api/v1/alerts/history", methods=["GET"])
@login_required
def alert_history_api():
    try:
        alert_data = AlertTicket.query.all()
        if not alert_data:
            return jsonify({"message": "No alert history found."}), 404

        return jsonify([alert.serialize() for alert in alert_data]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/chart-configurations")
@login_required
def get_chart_configurations():

    user_id = current_user.id
    user = UserProfile.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    chart_configurations = ChartConfiguration.query.filter_by(user_id=user_id).all()
    return jsonify([config.serialize() for config in chart_configurations])


@app.route("/api/v1/labels", methods=["GET"])
@login_required
def retrieve_labels():
    response = prometheus_api_client.get("/api/v1/label/__name__/values")
    data = response.json().get("data", [])
    return render_template("graphs/labels.html", labels=data)


@app.route("/api/v1/system/disk", methods=["GET"])
@login_required
def get_disk_usage():
    disk_info = disk_metrics.get_metrics
    return jsonify(disk_info)


@app.route("/api/v1/system/network", methods=["GET"])
@login_required
def get_network_metrics():
    network_data = network_metrics.get_metrics
    return jsonify(network_data)


def check_prometheus_health():
    try:
        response = prometheus_api_client.get("/api/v1/targets")
        if response.status_code == 200:
            return "healthy"
        else:
            return "unhealthy"
    except requests.exceptions.RequestException:
        return "unhealthy"

def check_alert_manager_health():
    # alert_manager_url = 'http://localhost:9093/api/v2/status'
    try:
        response = alertmanager_api_client.get("/api/v2/status")
        if response.status_code == 200:
            return "healthy"
        else:
            return "unhealthy"
    except requests.exceptions.RequestException:
        return "unhealthy"

@app.route('/api/v1/system/status', methods=['GET'])
@login_required
def get_status():
    total_services = 3
    running_services = 0

    # Check database status
    db_status = check_database()
    db_health = db_status.get('status', 'unknown')
    running_services += (db_health == 'healthy')

    # Check Prometheus health
    prometheus_health = check_prometheus_health()
    running_services += (prometheus_health == 'healthy')

    # check alert manager health
    alert_manager_health = check_alert_manager_health()
    running_services += (alert_manager_health == 'healthy')

    # Prepare the response
    status = {
        "service": {
            "total_services": total_services,
            "running_services": running_services,
            "db_health": db_health,
            "prometheus_health": prometheus_health,
            "alert_manager_health": alert_manager_health,
            "status": f"{running_services}/{total_services} Services Running",
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return jsonify(status), 200
