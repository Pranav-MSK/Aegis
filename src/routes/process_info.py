# cython: language_level=3
import os
import subprocess
from flask import (
    request,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    blueprints,
)
from flask_login import current_user, login_required
from src.config import app
from src.utils import get_top_processes, render_template_from_file, ROOT_DIR
from src.alert_manager import send_smtp_email
from src.config import get_app_info
from src.logger import logger
from src.routes.helper.common_helper import (
    admin_required,
    check_page_toggle,
    handle_sudo_password,
)

process_bp = blueprints.Blueprint("process", __name__)

@app.route("/process", methods=["GET", "POST"])
@check_page_toggle("is_process_info_enabled")
@admin_required
@handle_sudo_password("process")
@login_required
def process():
    number_of_processes = session.get("number_of_processes", 50)
    sort_by = request.args.get("sort", "cpu")
    order = request.args.get("order", "asc")
    toggle_order = "desc" if order == "asc" else "asc"

    sudo_password = session.get("sudo_password", "")

    if request.method == "POST":
        if "kill_pid" in request.form:
            pid_to_kill = request.form.get("kill_pid")
            process_name = request.form.get("process_name")

            if pid_to_kill and process_name:
                try:
                    result = subprocess.run(
                        ['sudo', '-S', 'kill', '-9', str(pid_to_kill)],
                        input=sudo_password + '\n',
                        stderr=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        text=True,
                    )

                    if result.returncode == 0:
                        flash(f"Process '{process_name}' (PID {pid_to_kill}) killed successfully.", "success")
                        logger.info(f"Killed process '{process_name}' (PID {pid_to_kill}) successfully by user '{current_user.username}' (IP: {request.remote_addr})")
                    else:
                        flash(f"Failed to kill process '{process_name}' (PID {pid_to_kill}). Error: {result.stderr.strip()}", "danger")
                        logger.error(f"Failed to kill process '{process_name}' (PID {pid_to_kill}). Error: {result.stderr.strip()}")
                except Exception as e:
                    flash(f"Error executing command: {str(e)}", "danger")
                    logger.error(f"Error executing command to kill process '{process_name}' (PID {pid_to_kill}): {str(e)}")
            else:
                flash("Invalid process ID or name.", "danger")
                logger.error("Invalid process ID or name.")
            return redirect(url_for("process"))

        # Handle the number of processes to display
        if "number" in request.form:
            number_of_processes = int(request.form.get("number", 50))
            session["number_of_processes"] = number_of_processes

    top_processes = get_top_processes(number_of_processes)

    sort_key = {
        "cpu": 1,
        "memory": 2,
        "name": 0,
    }.get(sort_by, 1)
    top_processes.sort(key=lambda x: x[sort_key], reverse=(order == "desc"))

    return render_template(
        "info_pages/process.html",
        processes=top_processes,
        number=number_of_processes,
        toggle_order=toggle_order,
    )

