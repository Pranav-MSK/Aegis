# cython: language_level=3
import subprocess
from flask import (
    request,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    blueprints,
    jsonify
)
from flask_login import current_user, login_required
from src.config.app_config import app, csrf
from src.helper.utils import get_top_processes
from src.helper.logger import get_logger
logger = get_logger(__name__)
from src.routes.helper.common_helper import (
    admin_required,
    handle_sudo_password,
)

process_bp = blueprints.Blueprint("process", __name__)

@app.route("/process", methods=["GET", "POST"])
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
                    # First, try to kill the process normally
                    result = subprocess.run(
                        ['sudo', '-S', 'kill', str(pid_to_kill)],
                        input=sudo_password + '\n',
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode != 0:
                        # If normal kill fails, try SIGKILL
                        result = subprocess.run(
                            ['sudo', '-S', 'kill', '-9', str(pid_to_kill)],
                            input=sudo_password + '\n',
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                    
                    if result.returncode == 0:
                        flash(f"Process '{process_name}' (PID {pid_to_kill}) killed successfully.", "success")
                        logger.info(f"Killed process '{process_name}' (PID {pid_to_kill}) successfully by user '{current_user.username}' (IP: {request.remote_addr})")
                    else:
                        # If both methods fail, check if the process still exists
                        check_process = subprocess.run(
                            ['ps', '-p', str(pid_to_kill)],
                            capture_output=True,
                            text=True
                        )
                        
                        if check_process.returncode != 0:
                            # Process doesn't exist, assume it was killed
                            flash(f"Process '{process_name}' (PID {pid_to_kill}) no longer exists. It may have been terminated.", "success")
                            logger.info(f"Process '{process_name}' (PID {pid_to_kill}) no longer exists. Assumed terminated.")
                        else:
                            # Process still exists, report failure
                            flash(f"Failed to kill process '{process_name}' (PID {pid_to_kill}). Error: {result.stderr.strip()}", "danger")
                            logger.error(f"Failed to kill process '{process_name}' (PID {pid_to_kill}). Error: {result.stderr.strip()}")
                
                except subprocess.TimeoutExpired:
                    flash(f"Timeout while attempting to kill process '{process_name}' (PID {pid_to_kill}).", "danger")
                    logger.error(f"Timeout while attempting to kill process '{process_name}' (PID {pid_to_kill}).")
                except Exception as e:
                    flash(f"Error executing command: {str(e)}", "danger")
                    logger.error(f"Error executing command to kill process '{process_name}' (PID {pid_to_kill}): {str(e)}")
            else:
                flash("Invalid process ID or name.", "danger")
                logger.error("Invalid process ID or name.")
        
        return redirect(url_for("process"))

    top_processes = get_top_processes(number_of_processes)

    sort_key = {
        "cpu": 1,
        "memory": 2,
        "name": 0,
    }.get(sort_by, 1)
    top_processes.sort(key=lambda x: x[sort_key], reverse=(order == "desc")) # type: ignore

    return render_template(
        "info_pages/process.html",
        processes=top_processes,
        number=number_of_processes,
        toggle_order=toggle_order,
    )

@app.route("/kill_process", methods=["POST"])
@csrf.exempt
@admin_required
def kill_process():
    sudo_password = session.get("sudo_password", "")
    if request.method == "POST":
        data = request.json
        pid_to_kill = data.get("kill_pid") # type: ignore
        process_name = data.get("process_name") # type: ignore

        if pid_to_kill and process_name:
            try:
                # First, try to kill the process normally
                result = subprocess.run(
                    ['sudo', '-S', 'kill', str(pid_to_kill)],
                    input=sudo_password + '\n',
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode != 0:
                    # If normal kill fails, try SIGKILL
                    result = subprocess.run(
                        ['sudo', '-S', 'kill', '-9', str(pid_to_kill)],
                        input=sudo_password + '\n',
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                if result.returncode == 0:
                    logger.info(f"Killed process '{process_name}' (PID {pid_to_kill}) successfully by user '{current_user.username}' (IP: {request.remote_addr})")
                    return jsonify({"success": True})
                else:
                    # If both methods fail, check if the process still exists
                    check_process = subprocess.run(
                        ['ps', '-p', str(pid_to_kill)],
                        capture_output=True,
                        text=True
                    )
                    
                    if check_process.returncode != 0:
                        # Process doesn't exist, assume it was killed
                        logger.info(f"Process '{process_name}' (PID {pid_to_kill}) no longer exists. Assumed terminated.")
                    else:
                        logger.error(f"Failed to kill process '{process_name}' (PID {pid_to_kill}). Error: {result.stderr.strip()}")
            
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout while attempting to kill process '{process_name}' (PID {pid_to_kill}).")
            except Exception as e:
                logger.error(f"Error executing command to kill process '{process_name}' (PID {pid_to_kill}): {str(e)}")
        else:
            logger.error("Invalid process ID or name.")
    
    return redirect(url_for("process"))