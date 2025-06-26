# cython: language_level=3
from datetime import datetime
from src.models.base_model import BaseModel
from src.core.config.app_config import db
from sqlalchemy.orm import relationship

class NotificationSettings(BaseModel):
    """
    Notification settings for Slack, Discord, and Teams.

    Attributes:
        - id: Notification ID
        - slack_webhook_url: Slack webhook URL
        - discord_webhook_url: Discord webhook URL
        - teams_webhook_url: Teams webhook URL
        - google_chat_webhook_url: Google Chat webhook URL
        - is_email_alert_enabled: True if email alerts are enabled
        - is_slack_alert_enabled: True if Slack alerts are enabled
        - is_discord_alert_enabled: True if Discord alerts are enabled
        - is_teams_alert_enabled: True if Teams alerts are enabled
        - is_google_chat_alert_enabled: True if Google Chat alerts are enabled

    Methods:
        - to_dict: Convert notification settings to a dictionary
        - get_slack_webhook_url: Get the Slack webhook URL
        - get_discord_webhook_url: Get the Discord webhook URL
        - get_teams_webhook_url: Get the Teams webhook URL
        - get_google_chat_webhook_url: Get the Google Chat webhook URL
        - get_telegram_webhook_url: Get the Telegram webhook URL
    """

    id = db.Column(db.Integer, primary_key=True)
    slack_webhook_url = db.Column(db.String(150), nullable=True)
    discord_webhook_url = db.Column(db.String(150), nullable=True)
    teams_webhook_url = db.Column(db.String(150), nullable=True)
    google_chat_webhook_url = db.Column(db.String(150), nullable=True)

    is_email_alert_enabled = db.Column(db.Boolean, default=False)
    is_slack_alert_enabled = db.Column(db.Boolean, default=False)
    is_discord_alert_enabled = db.Column(db.Boolean, default=False)
    is_teams_alert_enabled = db.Column(db.Boolean, default=False)
    is_google_chat_alert_enabled = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<NotificationSettings>"

    @staticmethod
    def to_dict():
        notification_settings = NotificationSettings.query.first()
        if notification_settings is None:
            return {
                "slack_webhook_url": None,
                "discord_webhook_url": None,
                "teams_webhook_url": None,
                "google_chat_webhook_url": None,
                "is_email_alert_enabled": False,
                "is_slack_alert_enabled": False,
                "is_discord_alert_enabled": False,
                "is_teams_alert_enabled": False,
                "is_google_chat_alert_enabled": False,
            }
        return {
            "slack_webhook_url": notification_settings.slack_webhook_url,
            "discord_webhook_url": notification_settings.discord_webhook_url,
            "teams_webhook_url": notification_settings.teams_webhook_url,
            "google_chat_webhook_url": notification_settings.google_chat_webhook_url,
            "is_email_alert_enabled": notification_settings.is_email_alert_enabled,
            "is_slack_alert_enabled": notification_settings.is_slack_alert_enabled,
            "is_discord_alert_enabled": notification_settings.is_discord_alert_enabled,
            "is_teams_alert_enabled": notification_settings.is_teams_alert_enabled,
            "is_google_chat_alert_enabled": notification_settings.is_google_chat_alert_enabled,
        }

    @staticmethod
    def get_slack_webhook_url():
        notification_settings = NotificationSettings.query.first()
        return notification_settings.slack_webhook_url if notification_settings else None

    @staticmethod
    def get_discord_webhook_url():
        notification_settings = NotificationSettings.query.first()
        # return NotificationSettings.query.first().discord_webhook_url
        return notification_settings.discord_webhook_url if notification_settings else None

    @staticmethod
    def get_teams_webhook_url():
        notification_settings = NotificationSettings.query.first()
        # return NotificationSettings.query.first().teams_webhook_url
        return notification_settings.teams_webhook_url if notification_settings else None

    @staticmethod
    def get_google_chat_webhook_url():
        notification_settings = NotificationSettings.query.first()
        # return NotificationSettings.query.first().google_chat_webhook_url
        return notification_settings.google_chat_webhook_url if notification_settings else None

    @staticmethod
    def get_telegram_webhook_url():
        notification_settings = NotificationSettings.query.first()
        # return NotificationSettings.query.first().telegram_webhook_url
        return notification_settings.telegram_webhook_url if notification_settings else None


# Notification model
class Notification(BaseModel):
    """
    Notification model for system notifications.
    
    Attributes:
        - id: Notification ID
        - type: Notification type (e.g., 'info', 'warning', 'error')
        - icon: Notification icon (e.g., 'info', 'warning', 'error')
        - title: Notification title
        - message: Notification message content
        - time: Notification timestamp
        - is_global: True for global notifications
    
    Relationships:
        - user_notifications: User notifications relationship

    Methods:
        - to_dict: Convert notification attributes to a dictionary

    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    is_global = db.Column(db.Boolean, default=False)  # True for global notifications

    user_notifications = relationship('SystemNotification', back_populates='notification')

    def __repr__(self):
        return f'<Notification {self.title}>'
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "icon": self.icon,
            "title": self.title,
            "message": self.message,
            "time": self.time,
            "is_global": self.is_global
        }

class SystemNotification(BaseModel):
    """ 
    System notification model to track read/unread notifications for users.

    Attributes:
        - user_id: User ID
        - notification_id: Notification ID
        - unread: True if notification is unread

    Relationships:
        - notification: Notification relationship

    Methods:
        - __repr__: Return a string representation of the object
    """

    __tablename__ = 'user_notifications'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.id'), primary_key=True)
    unread = db.Column(db.Boolean, default=True)

    notification = relationship('Notification', back_populates='user_notifications')

    def __repr__(self):
        return f'<SystemNotification user_id={self.user_id}, notification_id={self.notification_id}>'
