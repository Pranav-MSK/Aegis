from src.services.notification.observers.base_observer import AlertObserver

from src.infrastructure.messaging.slack_service import dispatch_slack_alert

class SlackAlertObserver(AlertObserver):

    def __init__(self, config):
        self.slack_webhook = config.get("slack_webhook_url")

    def notify(self, alert_instance):
        if self.slack_webhook:
            dispatch_slack_alert(self.slack_webhook, alert_instance)

