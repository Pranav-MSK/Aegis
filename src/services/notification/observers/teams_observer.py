# cython: language_level=3
from src.services.notification.observers.base_observer import AlertObserver

from src.infrastructure.messaging.team_service import dispatch_teams_alert

class TeamsAlertObserver(AlertObserver):

    def __init__(self, config):
        self.teams_webhook_url = config.get("teams_webhook_url")

    def notify(self, alert_instance):
        if self.teams_webhook_url:
            dispatch_teams_alert(self.teams_webhook_url, alert_instance)
