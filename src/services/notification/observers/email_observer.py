import os
from src.services.notification.observers.base_observer import AlertObserver

from src.services.messaging.email_service import send_smtp_email
from src.services.common_helper import get_email_addresses
from src.helper.template_utils import render_template_from_file
from src.helper.basic_info import ROOT_DIR

class EmailAlertObserver(AlertObserver):

    def notify(self, alert_instance):
        admin_emails = get_email_addresses(user_level="admin", receive_email_alerts=True)
        if not admin_emails:
            return
        context = {
            "alert_name": alert_instance.alert_name,
            "instance": alert_instance.instance,
            "severity": alert_instance.severity,
            "description": alert_instance.description,
            "summary": alert_instance.summary,
        }
        email_body = render_template_from_file(
            os.path.join(ROOT_DIR, "src/templates/email_templates/alert_template.html"),
            **context
        )
        send_smtp_email(
            receiver_email=admin_emails,
            subject=f"{alert_instance.alert_name} Alert",
            body=email_body,
            is_html=True,
        )
