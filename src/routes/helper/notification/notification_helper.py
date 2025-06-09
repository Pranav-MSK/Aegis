# cython: language_level=3
import os

from src.logger import get_logger
logger = get_logger(__name__)

from src.models import (
    NotificationSettings)

from src.alert_manager import (
    send_slack_alert,
    send_smtp_email,
    send_discord_alert,
    send_teams_alert,
    send_google_chat_alert,
)

from src.routes.helper.common_helper import get_email_addresses
from src.utils import render_template_from_file, ROOT_DIR

from abc import ABC, abstractmethod

# NOTE: Abstract Base Class for Alert Observers
# This class defines the interface for all alert observers.
# Each concrete observer must implement the `notify` method,
# Easily extensible for adding new notification methods in the future.
class AlertObserver(ABC):
    """
    Abstract base class for alert observers.
    Concrete observers should implement the `notify` method.
    """

    @abstractmethod
    def notify(self, alert_instance):
        """
        Notify the observer with the alert instance.
        """
        pass


class SlackAlertObserver(AlertObserver):
    def __init__(self, config):
        self.slack_webhook = config.get("slack_webhook_url")
    def notify(self, alert_instance):
        if self.slack_webhook:
            send_slack_alert(self.slack_webhook, alert_instance)


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


class DiscordAlertObserver(AlertObserver):
    def __init__(self, config):
        self.discord_webhook = config.get("discord_webhook_url")
    def notify(self, alert_instance):
        if self.discord_webhook:
            send_discord_alert(self.discord_webhook, alert_instance)


class TeamsAlertObserver(AlertObserver):
    def __init__(self, config):
        self.teams_webhook_url = config.get("teams_webhook_url")
    def notify(self, alert_instance):
        if self.teams_webhook_url:
            send_teams_alert(self.teams_webhook_url, alert_instance)


class GoogleChatAlertObserver(AlertObserver):
    def __init__(self, config):
        self.google_chat_webhook_url = config.get("google_chat_webhook_url")
    def notify(self, alert_instance):
        if self.google_chat_webhook_url:
            send_google_chat_alert(self.google_chat_webhook_url, alert_instance)

# NOTE - Design Pattern: Factory Method
# This factory creates instances of alert observers based on the notification configuration.
# It encapsulates the logic for determining which observers to create,
# allowing for easy extension and modification of alert notification mechanisms.
class AlertObserverFactory:
    @staticmethod
    def create_observers(notification_config):
        observers = []
        if notification_config.get("is_email_alert_enabled"):
            observers.append(EmailAlertObserver())
        if notification_config.get("is_slack_alert_enabled"):
            observers.append(SlackAlertObserver(notification_config))
        if notification_config.get("is_discord_alert_enabled"):
            observers.append(DiscordAlertObserver(notification_config))
        if notification_config.get("is_teams_alert_enabled"):
            observers.append(TeamsAlertObserver(notification_config))
        if notification_config.get("is_google_chat_alert_enabled"):
            observers.append(GoogleChatAlertObserver(notification_config))
        return observers

# NOTE: Design Pattern: Observer
# This class is responsible for notifying all registered observers about an alert instance.
# It iterates through the list of observers and calls their `notify` method,
# allowing each observer to handle the alert instance as needed.
class AlertNotifier:
    def __init__(self, observers: list[AlertObserver]):
        self._observers = observers

    def notify_all(self, alert_instance):
        for observer in self._observers:
            try:
                observer.notify(alert_instance)
            except Exception as e:
                logger.error(f"Error notifying {observer.__class__.__name__}: {e}")

    def get_observers(self):
        return self._observers
    

def notify_alert(alert_instance):
    notification_config = NotificationSettings().to_dict()
    observers = AlertObserverFactory.create_observers(notification_config)
    notifier = AlertNotifier(observers)
    notifier.notify_all(alert_instance)
