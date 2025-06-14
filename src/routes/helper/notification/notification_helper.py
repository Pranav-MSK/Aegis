# cython: language_level=3
import os

from src.helper.logger import get_logger
logger = get_logger(__name__)

from src.models import (
    NotificationSettings)

from src.routes.helper.notification.observers import (
    EmailAlertObserver,
    SlackAlertObserver,
    DiscordAlertObserver,
    TeamsAlertObserver,
    GoogleChatAlertObserver
)

from src.routes.helper.notification.manager import generate_system_notification
from src.schemas.discussion_board import UserNotification   

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


class SystemNotificationObserver(AlertObserver):
    """ In App Notification Observer

    this observer is responsible for generating system notifications
    that show up in the application interface.
    """

    def notify(self, alert_instance):
       
        notification_data = UserNotification(
            type=alert_instance.severity,
            icon="info-circle",
            title=alert_instance.alert_name,
            message=alert_instance.description,
            is_global=True
        )
        generate_system_notification(notification_data)

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
        # system notification observer is default on
        observers.append(SystemNotificationObserver())

        return observers

# NOTE: Design Pattern: Observer
# This class is responsible for notifying all registered observers about an alert instance.
# It iterates through the list of observers and calls their `notify` method,
# allowing each observer to handle the alert instance as needed.
class AlertNotifier:

    def __init__(self):
        self._observers = []

    def fetch_observers(self):
        """
        Fetches observers based on the notification configuration.
        """
        notification_config = NotificationSettings().to_dict()
        self._observers = AlertObserverFactory.create_observers(notification_config)

    def notify_all(self, alert_instance):
        self.fetch_observers()
        for observer in self._observers:
            try:
                observer.notify(alert_instance)
            except Exception as e:
                logger.error(f"Error notifying {observer.__class__.__name__}: {e}")
