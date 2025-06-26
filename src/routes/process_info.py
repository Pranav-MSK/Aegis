from flask import (
    request,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    Blueprint,
    jsonify,
)
from flask_login import current_user, login_required
from src.config.app_config import app, csrf
from src.services.common_helper import (
    admin_required,
    handle_sudo_password,
)
from src.services.process_service import ProcessService

process_bp = Blueprint("process", __name__)

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
                success, message = ProcessService.kill_process(
                    pid_to_kill=pid_to_kill,
                    process_name=process_name,
                    sudo_password=sudo_password,
                    user=current_user.username,
                    remote_addr=request.remote_addr,
                )
                flash(message, "success" if success else "danger")
            else:
                flash("Invalid process ID or name.", "danger")
        return redirect(url_for("process"))

    processes = ProcessService.get_processes(number_of_processes, sort_by, order)
    return render_template(
        "info_pages/process.html",
        processes=processes,
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
        pid_to_kill = data.get("kill_pid") if data else None
        process_name = data.get("process_name") if data else None
        if pid_to_kill and process_name:
            success, message = ProcessService.kill_process(
                pid_to_kill=pid_to_kill,
                process_name=process_name,
                sudo_password=sudo_password,
                user=current_user.username,
                remote_addr=request.remote_addr,
            )
            return jsonify({"success": success, "message": message})
        else:
            return jsonify({"success": False, "message": "Invalid process ID or name."})
    return redirect(url_for("process"))