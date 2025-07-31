# cython: language_level=3
from src.services.notification.observers.base_observer import AlertObserver

from src.infrastructure.messaging.google_chat_service import dispatch_google_chat_notification

class GoogleChatAlertObserver(AlertObserver):

    def __init__(self, config):
        self.google_chat_webhook_url = config.get("google_chat_webhook_url")

    def notify(self, alert_instance):
        if self.google_chat_webhook_url:
            dispatch_google_chat_notification(self.google_chat_webhook_url, alert_instance)