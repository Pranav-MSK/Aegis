# cython: language_level=3
from flask import render_template, request, flash, redirect, url_for, blueprints

from src.config.app_config import app, db
from src.models import SMTPSettings
from src.services.common_helper import admin_required

smtp_email_config_bp = blueprints.Blueprint('smtp_email_config', __name__)


@app.route("/update-email-password", methods=["GET", "POST"])
@admin_required
def smtp_config():
    smtp_config = SMTPSettings.query.first()

    if request.method == "POST":
        username = request.form.get("username")
        new_password = request.form.get("password")
        smtp_server = request.form.get("smtp_server")
        smtp_port = request.form.get("smtp_port")
        email_from = request.form.get("email_from")


        if not username or not new_password:
            flash("Please provide email and password.", "danger")
            return redirect(url_for("smtp_config"))
        
        
        if not smtp_config:
            smtp_config = SMTPSettings(username=username, password=new_password, # type: ignore
                                       smtp_server=smtp_server, smtp_port=smtp_port, # type: ignore
                                       email_from=email_from) # type: ignore
            db.session.add(smtp_config)
        else:
            smtp_config.username = username
            smtp_config.password = new_password        
        
        smtp_config.save()
        flash("Email and password updated successfully!", "success")
        return redirect(url_for("smtp_config"))

    return render_template("other/smtp_config.html", smtp_config=smtp_config)
