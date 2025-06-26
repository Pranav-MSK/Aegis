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
from flask_login import login_required

from src.config.app_config import app, get_app_info
from src.models import UserProfile
from src.helper.basic_info import ROOT_DIR
from src.helper.logger import get_logger
from src.routes.helper.common_helper import admin_required
from src.routes.helper.prometheus_helper import (
    load_yaml,
    save_yaml,
    show_targets,
    prometheus_yml_path,
    update_prometheus_config,
    save_updated_alert_manager_config,
    retrieve_active_alerts,
    retrieve_active_alertmanagers,
    count_of_targets,
    calculate_total_rules,
)
from src.services.decorators.access_decorators import systemguard_enterprise
from src.config.config_loader import configuration_settings
from clients.http_client.client import HttpClient

prometheus_api_client = HttpClient("prometheus")
logger = get_logger(__name__)
# Define the Prometheus Blueprint
prometheus_bp = Blueprint("prometheus", __name__)

PROMETHEUS_RELOAD_URL = configuration_settings.get(
    "monitoring.prometheus", "RELOAD_URL"
)

RULES_FILE_PATH = os.path.join(ROOT_DIR, "prometheus_config/alert_rules.yml")

def reload_prometheus(prometheus_url="http://localhost:9090/-/reload"):
    """
    Triggers a reload of Prometheus configuration and alert rules.

    Args:
        prometheus_url (str): The URL for the Prometheus reload endpoint.

    Returns:
        bool: True if reload was successful (HTTP 200), False otherwise.
        str: The response text from Prometheus.
    """
    try:
        response = requests.post(prometheus_url, timeout=5)
        if response.status_code == 200:
            return True, "Prometheus reloaded successfully."
        else:
            return False, f"Reload failed with status {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {e}"
    
# Cache user queries with LRU cache (memory-based, not ideal for distributed apps)
@lru_cache(maxsize=128)
def get_user_by_username(username):
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
    if not verify_user(auth.username, auth.password): # type: ignore
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

# #NOTE - Need to remove this route in production
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

@app.route("/system/targets", methods=["GET", "POST", "PUT", "DELETE"])
@systemguard_enterprise()
@admin_required
def configure_targets():
    update_prometheus_config()
    save_updated_alert_manager_config()
    targets_info = show_targets()
    total_targets = count_of_targets()

    if request.form.get("_method") == "POST":
        max_scrap_target = get_app_info().get("max_scrap_target")
        if max_scrap_target is not None and total_targets >= max_scrap_target:
            flash(
                f"Cannot add more targets. You have reached the maximum limit of {max_scrap_target} targets.",
                "danger",
            )
            logger.error(
                f"Cannot add more targets. You have reached the maximum limit of {max_scrap_target} targets."
            )
            return redirect(url_for("configure_targets"))

        job_name = request.form.get("job_name")
        new_target = request.form.get("new_target")
        username = request.form.get("username")
        password = request.form.get("password")
        scrape_interval = (
            request.form.get("scrape_interval", "15s") + "s"
        )  # New scrape interval
        config = load_yaml(prometheus_yml_path)

        # Validate target format
        if not new_target or ":" not in new_target:
            flash(
                "Invalid target format. It should be in the format <ip>:<port>.",
                "danger",
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
        reload_prometheus()

        return redirect(url_for("configure_targets"))

    if request.form.get("_method") == "DELETE":
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
                        f"Target {target_to_remove} not found in job {job_name}.",
                        "warning",
                    )
                break

        for index, j in enumerate(config["scrape_configs"]):
            config["scrape_configs"][index] = OrderedDict(j)

        else:
            flash(f"Job {job_name} not found.", "warning")

        save_yaml(config, prometheus_yml_path)
        reload_prometheus()
        return redirect(url_for("configure_targets"))

    if request.form.get("_method") == "PUT":
        if request.form.get("action") == "update_interval":
            job_name = request.form.get("job_name")
            new_interval = (request.form.get("new_interval") or "15") + "s"  # New scrape interval
            config = load_yaml(prometheus_yml_path)

            for scrape_config in config["scrape_configs"]:
                if scrape_config["job_name"] == job_name:
                    scrape_config["scrape_interval"] = new_interval
                    flash("Scrape interval updated successfully!", "success")
                    break

            for index, j in enumerate(config["scrape_configs"]):
                config["scrape_configs"][index] = OrderedDict(j)

            save_yaml(config, prometheus_yml_path)
            return redirect(url_for("configure_targets"))

        elif request.form.get("action") == "update_auth":
            job_name = request.form.get("job_name")
            username = request.form.get("username")
            password = request.form.get("password")
            config = load_yaml(prometheus_yml_path)

            found = False
            for scrape_config in config["scrape_configs"]:
                if scrape_config["job_name"] == job_name:
                    found = True
                    if username and password:
                        scrape_config["basic_auth"] = {
                            "username": username,
                            "password": password,
                        }
                    flash("Basic Auth updated successfully!", "success")
                    break

            if not found:
                flash(f"Job {job_name} not found.", "warning")

            for index, j in enumerate(config["scrape_configs"]):
                config["scrape_configs"][index] = OrderedDict(j)

            save_yaml(config, prometheus_yml_path)
            return redirect(url_for("configure_targets"))

    return render_template(
        "system/targets.html",
        targets_info=targets_info,
        total_targets=total_targets
    )


@app.route("/system/targets/restart_prometheus")
@admin_required
def restart_prometheus():
    reload_prometheus()
    flash("Prometheus service updated successfully!", "success")
    return redirect(url_for("configure_targets"))



@app.route("/api/v1/alerts/active", methods=["GET"])
@login_required
def api_active_alerts():
    try:
        alerts = retrieve_active_alerts()
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# prometheus active alerts
@app.route("/system/alerts/active")
@login_required
def active_alerts():
    try:
        alerts = retrieve_active_alerts()
    except Exception as e:
        alerts = []
    return render_template("alerts/active_alerts.html", alerts=alerts)


@app.route("/api/v1/system/alerts/rules", methods=["GET"])
@login_required
def prometheus_rules_api():
    # Load existing rules from the YAML file
    with open(RULES_FILE_PATH, "r") as file:
        rules = yaml.safe_load(file)

    # Return the rules as JSON
    return jsonify(rules)

@app.route("/system/alerts/rules", methods=["GET", "POST"])
@systemguard_enterprise()
@admin_required
def manage_rules():
    # Load existing rules from the YAML file
    with open(RULES_FILE_PATH, "r") as file:
        rules = yaml.safe_load(file)

    total_rules = calculate_total_rules()

    if request.method == "POST":
        action = request.form.get("action")
        group_name = request.form.get("group_name")

        if action == "add":
            max_alert_rules = get_app_info().get("max_alert_rules")
            if max_alert_rules is not None and total_rules >= max_alert_rules:
                flash(
                    f"Cannot add more rules. You have reached the maximum limit of {max_alert_rules} rules.",
                    "danger",
                )
                logger.error(
                    f"Cannot add more rules. You have reached the maximum limit of {max_alert_rules} rules."
                )
                return redirect(url_for("manage_rules"))

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
            for group in rules["groups"]:
                if group["name"] == group_name:
                    group["rules"].append(new_rule)
                    break

            # Write the updated rules back to the file
            with open(RULES_FILE_PATH, "w") as file:
                yaml.dump(rules, file)

            # Reload Prometheus configuration
            reload_prometheus()

            flash("Rule added successfully!", "success")
            return redirect(url_for("manage_rules"))

        elif action == "edit":
            # index = int(request.form.get("index"))

            index_str = request.form.get("index")
            if index_str is None:
                flash("No rule index provided.", "danger")
                return redirect(url_for("manage_rules"))
            index = int(index_str)
                

            # Find the group and edit the specified rule
            for group in rules["groups"]:
                if group["name"] == group_name and index < len(group["rules"]):
                    group["rules"][index]["expr"] = request.form.get("expr")
                    group["rules"][index]["for"] = request.form.get("for")
                    group["rules"][index]["labels"]["severity"] = request.form.get(
                        "severity"
                    )
                    group["rules"][index]["annotations"]["description"] = (
                        request.form.get("description")
                    )
                    group["rules"][index]["annotations"]["summary"] = request.form.get(
                        "summary"
                    )
                    group["rules"][index]["annotations"]["runbook_url"] = (
                        request.form.get("runbook_url")
                    )
                    break

            # Write the updated rules back to the file
            with open(RULES_FILE_PATH, "w") as file:
                yaml.dump(rules, file)

            # Reload Prometheus configuration
            # requests.post(PROMETHEUS_RELOAD_URL)
            reload_prometheus()

            flash("Rule updated successfully!", "success")
            return redirect(url_for("manage_rules"))

        elif action == "delete":
            # index = int(request.form.get("index"))
            index_str = request.form.get("index")
            if index_str is None:
                flash("No rule index provided.", "danger")
                return redirect(url_for("manage_rules"))
            index = int(index_str)
            

            # Find the group and delete the specified rule
            for group in rules["groups"]:
                if group["name"] == group_name and index < len(group["rules"]):
                    group["rules"].pop(index)
                    break

            # Write the updated rules back to the file
            with open(RULES_FILE_PATH, "w") as file:
                yaml.dump(rules, file)

            # Reload Prometheus configuration
            # requests.post(PROMETHEUS_RELOAD_URL)
            reload_prometheus()

            flash("Rule deleted successfully!", "success")
            return redirect(url_for("manage_rules"))

    return render_template(
        "alerts/view_rules.html", rules=rules, total_rules=total_rules
    )


@app.route("/system/alertmanager/status")
@login_required
def alertmanager_status():
    active_alertmanagers = retrieve_active_alertmanagers()
    if active_alertmanagers:
        return render_template(
            "alerts/alertmanager_status.html", alertmanagers=active_alertmanagers
        )

    return jsonify({"error": "Unable to fetch Alertmanager status"}), 500


@app.route('/api/v1/alertmanagers', methods=['GET'])
@login_required
def api_alertmanagers():
    try:
        response = prometheus_api_client.get("/api/v1/alertmanagers")
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500