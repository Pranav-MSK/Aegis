# cython: language_level=3
from flask import (
    Blueprint,
    Response,
    request,
    render_template,
    flash,
    redirect,
    url_for,
    jsonify,
)
from prometheus_client import generate_latest
import os
import yaml
import requests
from collections import OrderedDict
from werkzeug.security import check_password_hash

from functools import lru_cache
from flask import g  # 'g' is a request-specific object
from src.config import app, db
from src.models import ExternalMonitornig, UserProfile
from src.utils import ROOT_DIR
from src.routes.helper.common_helper import admin_required
from src.routes.helper.prometheus_helper import (
    load_yaml,
    save_yaml,
    is_valid_file,
    show_targets,
    prometheus_yml_path,
    update_prometheus_container,
    update_prometheus_config,
    save_updated_alert_manager_config,
    fetch_active_alerts
)

# Define the Prometheus Blueprint
prometheus_bp = Blueprint("prometheus", __name__)

PROMETHEUS_BASE_URL = "http://localhost:9090"
ALERTMANAGER_BASE_URL = "http://localhost:9093"
PROMETHEUS_RELOAD_URL = "http://localhost:9090/api/v1/admin/tsdb/reload"  # Adjust as necessary
RULES_FILE_PATH = os.path.join(ROOT_DIR, "prometheus_config/alert_rules.yml")

# Cache user queries with LRU cache (memory-based, not ideal for distributed apps)
@lru_cache(maxsize=128)
def get_user_by_username(username):
    print("Querying the database...")
    # return UserProfile.query.filter_by(username=username).first()
    return UserProfile.get_by_username(username)


# Verify user login information
def verify_user(username, password):
    user = get_user_by_username(username)
    if user and check_password_hash(user.password, password):
        return True
    return False


# Define a route to serve Prometheus metrics
@app.route("/metrics")
def metrics():
    auth = request.authorization
    if not verify_user(auth.username, auth.password):
        return Response(
            "Could not verify",
            401,
            {"WWW-Authenticate": 'Basic realm="Login required"'},
        )
    output = generate_latest()
    output = "\n".join(
        [
            line
            for line in output.decode().split("\n")
            if not line.startswith("#") and line
        ]
    )
    return Response(output, mimetype="text/plain")

@app.route("/metrics_")
def metrics_():
    output = generate_latest()
    output = "\n".join(
        [
            line
            for line in output.decode().split("\n")
            if not line.startswith("#") and line
        ]
    )
    return Response(output, mimetype="text/plain")


# POST request to manage file paths
@app.route("/external_monitoring", methods=["GET", "POST"])
@admin_required
def external_monitoring():
    if request.method == "POST":
        file_path = request.form.get("file_path")

        if not os.path.exists(file_path):
            flash("File path does not exist", "danger")
            return redirect(url_for("external_monitoring"))

        # Check file path and validity
        if not is_valid_file(file_path):
            flash(
                "Invalid file format. File should have key-value pairs separated by a colon.",
                "danger",
            )
            return redirect(url_for("external_monitoring"))

        # Save into the ExternalMonitoring table
        new_task = ExternalMonitornig(file_path=file_path)
        new_task.save()

        return redirect(url_for("external_monitoring"))

    data = ExternalMonitornig.query.all()
    return render_template("prometheus/external_monitoring.html", data=data)


# POST request to delete file path
@app.route("/external_monitoring/delete_file_path/<int:id>", methods=["POST"])
@admin_required
def delete_file_path(id):
    file_path = ExternalMonitornig.query.get_or_404(id)
    file_path.delete()
    flash("File path deleted successfully!", "success")
    return redirect(url_for("external_monitoring"))


@app.route("/configure_targets")
@admin_required
def configure_targets():
    update_prometheus_config()
    save_updated_alert_manager_config()
    targets_info = show_targets()
    return render_template("prometheus/targets.html", targets_info=targets_info)


@app.route("/targets/restart_prometheus")
@admin_required
def restart_prometheus():
    update_prometheus_container()
    flash("Prometheus container restarted successfully!", "success")
    return redirect(url_for("configure_targets"))


@app.route("/targets/add_target", methods=["POST"])
def add_target():
    job_name = request.form.get("job_name")
    new_target = request.form.get("new_target")
    username = request.form.get("username")
    password = request.form.get("password")
    scrape_interval = (
        request.form.get("scrape_interval", "15s") + "s"
    )  # New scrape interval
    config = load_yaml(prometheus_yml_path)

    # Validate target format
    if ":" not in new_target:
        flash(
            "Invalid target format. It should be in the format <ip>:<port>.", "danger"
        )
        return redirect(url_for("configure_targets"))

    job_found = False

    # if job name already exists, add new target to the job
    for scrape_config in config["scrape_configs"]:
        if scrape_config["job_name"] == job_name:
            # Append new target
            scrape_config["static_configs"][0]["targets"].append(new_target)
            job_found = True

            # Update scrape interval
            scrape_config["scrape_interval"] = scrape_interval

            # Prepare the updated job dictionary to maintain order
            updated_job = OrderedDict()
            updated_job["job_name"] = scrape_config["job_name"]
            updated_job["static_configs"] = scrape_config["static_configs"]
            updated_job["scrape_interval"] = scrape_config["scrape_interval"]
            updated_job["basic_auth"] = scrape_config.get("basic_auth", None)

            # Replace the existing job with the updated one
            index = config["scrape_configs"].index(scrape_config)
            config["scrape_configs"][index] = updated_job

            break

    if not job_found:
        # Create new job entry
        new_job = OrderedDict()
        new_job["job_name"] = job_name
        new_job["static_configs"] = [{"targets": [new_target]}]
        new_job["scrape_interval"] = scrape_interval

        # Add basic_auth if provided
        if username and password:
            new_job["basic_auth"] = {"username": username, "password": password}
        # Append the new job to scrape_configs
        config["scrape_configs"].append(new_job)

    for index, j in enumerate(config["scrape_configs"]):
        config["scrape_configs"][index] = OrderedDict(j)

    # Save the updated config
    save_yaml(config, prometheus_yml_path)
    flash("Target added successfully!", "success")
    return redirect(url_for("configure_targets"))


@app.route("/targets/remove_target", methods=["POST"])
@admin_required
def remove_target():
    job_name = request.form.get("job_name")
    target_to_remove = request.form.get("target_to_remove")
    config = load_yaml(prometheus_yml_path)

    for scrape_config in config["scrape_configs"]:
        if scrape_config["job_name"] == job_name:
            targets = scrape_config["static_configs"][0]["targets"]
            if target_to_remove in targets:
                targets.remove(target_to_remove)
                flash(f"Target {target_to_remove} removed successfully!", "success")

                # Check if this was the last target, then remove the job
                if not targets:  # If the list is now empty
                    config["scrape_configs"].remove(scrape_config)
                    flash(
                        f"Job {job_name} removed because it had no targets left.",
                        "success",
                    )
            else:
                flash(
                    f"Target {target_to_remove} not found in job {job_name}.", "warning"
                )
            break

    for index, j in enumerate(config["scrape_configs"]):
        config["scrape_configs"][index] = OrderedDict(j)

    else:
        flash(f"Job {job_name} not found.", "warning")

    save_yaml(config, prometheus_yml_path)
    # update_prometheus_container()
    return redirect(url_for("configure_targets"))


@app.route("/targets/change_interval", methods=["POST"])
@admin_required
def change_interval():
    job_name = request.form.get("job_name")
    new_interval = request.form.get("new_interval") + "s"  # New scrape interval
    config = load_yaml(prometheus_yml_path)

    for scrape_config in config["scrape_configs"]:
        if scrape_config["job_name"] == job_name:
            scrape_config["scrape_interval"] = new_interval
            flash("Scrape interval updated successfully!", "success")
            break

    for index, j in enumerate(config["scrape_configs"]):
        config["scrape_configs"][index] = OrderedDict(j)

    save_yaml(config, prometheus_yml_path)
    # update_prometheus_container()
    return redirect(url_for("configure_targets"))


# change username and password
@app.route("/targets/change_auth", methods=["POST"])
@admin_required
def change_auth():
    job_name = request.form.get("job_name")
    username = request.form.get("username")
    password = request.form.get("password")
    config = load_yaml(prometheus_yml_path)

    found = False
    for scrape_config in config["scrape_configs"]:
        if scrape_config["job_name"] == job_name:
            found = True
            if username and password:
                scrape_config["basic_auth"] = {"username": username, "password": password}
            flash("Basic Auth updated successfully!", "success")
            break

    if not found:
        flash(f"Job {job_name} not found.", "warning")

    for index, j in enumerate(config["scrape_configs"]):
        config["scrape_configs"][index] = OrderedDict(j)

    save_yaml(config, prometheus_yml_path)
    # update_prometheus_container()
    return redirect(url_for("configure_targets"))


# prometheus active alerts
@app.route("/active_alerts")
def active_alerts():
    try:
        alerts = fetch_active_alerts()
    except Exception as e:
        alerts = []
        print(f"Error fetching alerts: {e}")
    return render_template("alerts/active_alerts.html", alerts=alerts)


# alertmanager alerts
@app.route("/show_alerts")
def show_alerts():
    try:
        response = requests.get(f"{ALERTMANAGER_BASE_URL}/api/v2/alerts")
        response.raise_for_status()  # Raise an error for bad responses
        alerts = response.json()  # Parse JSON response

        return render_template("alerts/show_alerts.html", alerts=alerts)
    except requests.exceptions.RequestException as e:
        return f"Error fetching alerts: {str(e)}", 500


@app.route("/view_rules", methods=["GET", "POST"])
def view_rules():
    # Load existing rules from the YAML file
    with open(RULES_FILE_PATH, 'r') as file:
        rules = yaml.safe_load(file)

    if request.method == "POST":
        action = request.form.get("action")
        group_name = request.form.get("group_name")

        if action == "add":
            new_rule = {
                "alert": request.form.get("alert_name"),
                "expr": request.form.get("expr"),
                "for": request.form.get("for"),
                "labels": {
                    "severity": request.form.get("severity"),
                },
                "annotations": {
                    "description": request.form.get("description"),
                    "summary": request.form.get("summary"),
                    "runbook_url": request.form.get("runbook_url"),
                },
            }
            # Adding new rule logic
            for group in rules['groups']:
                if group['name'] == group_name:
                    group['rules'].append(new_rule)
                    break

            # Write the updated rules back to the file
            with open(RULES_FILE_PATH, 'w') as file:
                yaml.dump(rules, file)

            # Reload Prometheus configuration
            requests.post(PROMETHEUS_RELOAD_URL)

            flash("Rule added successfully!", "success")
            return redirect(url_for("view_rules"))

        elif action == "edit":
            index = int(request.form.get("index"))

            # Find the group and edit the specified rule
            for group in rules['groups']:
                if group['name'] == group_name and index < len(group['rules']):
                    group['rules'][index]["expr"] = request.form.get("expr")
                    group['rules'][index]["for"] = request.form.get("for")
                    group['rules'][index]["labels"]["severity"] = request.form.get("severity")
                    group['rules'][index]["annotations"]["description"] = request.form.get("description")
                    group['rules'][index]["annotations"]["summary"] = request.form.get("summary")
                    group['rules'][index]["annotations"]["runbook_url"] = request.form.get("runbook_url")
                    break

            # Write the updated rules back to the file
            with open(RULES_FILE_PATH, 'w') as file:
                yaml.dump(rules, file)

            # Reload Prometheus configuration
            requests.post(PROMETHEUS_RELOAD_URL)

            flash("Rule updated successfully!", "success")
            return redirect(url_for("view_rules"))

        elif action == "delete":
            index = int(request.form.get("index"))

            # Find the group and delete the specified rule
            for group in rules['groups']:
                if group['name'] == group_name and index < len(group['rules']):
                    group['rules'].pop(index)
                    break

            # Write the updated rules back to the file
            with open(RULES_FILE_PATH, 'w') as file:
                yaml.dump(rules, file)

            # Reload Prometheus configuration
            requests.post(PROMETHEUS_RELOAD_URL)

            flash("Rule deleted successfully!", "success")
            return redirect(url_for("view_rules"))

    return render_template("alerts/view_rules.html", rules=rules)

@app.route("/alertmanager/status")
def alertmanager_status():
    url = f"{PROMETHEUS_BASE_URL}/api/v1/alertmanagers"
    response = requests.get(url)

    if response.status_code == 200:
        alertmanager_data = response.json()
        active_alertmanagers = alertmanager_data["data"]["activeAlertmanagers"]
        return render_template(
            "alerts/alertmanager_status.html", alertmanagers=active_alertmanagers
        )
    else:
        return jsonify({"error": "Unable to fetch Alertmanager status"}), 500
