from src.services.notification.observers.base_observer import AlertObserver

from src.alert_manager import (
    send_google_chat_alert
)

class GoogleChatAlertObserver(AlertObserver):

    def __init__(self, config):
        self.google_chat_webhook_url = config.get("google_chat_webhook_url")

    def notify(self, alert_instance):
        if self.google_chat_webhook_url:
            send_google_chat_alert(self.google_chat_webhook_url, alert_instance)