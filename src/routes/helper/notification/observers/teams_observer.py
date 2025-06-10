from src.routes.helper.notification.observers.base_observer import AlertObserver

from src.alert_manager import (
    send_teams_alert
)

class TeamsAlertObserver(AlertObserver):

    def __init__(self, config):
        self.teams_webhook_url = config.get("teams_webhook_url")

    def notify(self, alert_instance):
        if self.teams_webhook_url:
            send_teams_alert(self.teams_webhook_url, alert_instance)
