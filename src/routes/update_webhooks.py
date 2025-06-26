# cython: language_level=3
from flask import render_template, request, redirect, url_for, flash, Blueprint
from src.config.app_config import app
from src.services.common_helper import admin_required
from src.services.webhook_service import get_settings_data, update_webhook_settings

webhooks_bp = Blueprint("webhooks", __name__)


@app.route("/update-webhooks", methods=["GET", "POST"])
@admin_required
def update_webhooks():
    if request.method == "POST":
        form_data = request.form.to_dict()
        update_webhook_settings(form_data)
        flash("Webhook settings updated successfully!", "success")
        return redirect(url_for("update_webhooks"))

    webhook_settings, enable_alerts = get_settings_data()
    return render_template(
        "settings/update_webhooks.html",
        webhook_settings=webhook_settings,
        enable_alerts=enable_alerts
    )
