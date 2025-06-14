from src.services import notification
from src.services.notification.observers.base_observer import AlertObserver

from src.services.messaging.discord_service import dispatch_alert_to_discord

class DiscordAlertObserver(AlertObserver):

    def __init__(self, config):
        self.discord_webhook = config.get("discord_webhook_url")

    def notify(self, alert_instance):
        if self.discord_webhook:
            dispatch_alert_to_discord(self.discord_webhook, alert_instance)
