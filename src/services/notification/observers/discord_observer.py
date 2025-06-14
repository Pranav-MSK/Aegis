from src.services.notification.observers.base_observer import AlertObserver

from src.alert_manager import send_discord_alert

class DiscordAlertObserver(AlertObserver):

    def __init__(self, config):
        self.discord_webhook = config.get("discord_webhook_url")

    def notify(self, alert_instance):
        if self.discord_webhook:
            send_discord_alert(self.discord_webhook, alert_instance)
