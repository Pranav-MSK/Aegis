# cython: language_level=3
from datetime import datetime
from src.models.base_model import BaseModel
from src.config import db

class NotificationSettings(BaseModel):
    """
    Notification settings for Slack, Discord, and Teams.
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
        return NotificationSettings.query.first().slack_webhook_url

    @staticmethod
    def get_discord_webhook_url():
        return NotificationSettings.query.first().discord_webhook_url

    @staticmethod
    def get_teams_webhook_url():
        return NotificationSettings.query.first().teams_webhook_url

    @staticmethod
    def get_google_chat_webhook_url():
        return NotificationSettings.query.first().google_chat_webhook_url

    @staticmethod
    def get_telegram_webhook_url():
        return NotificationSettings.query.first().telegram_webhook_url


# Notification model
class Notification(BaseModel):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    is_global = db.Column(db.Boolean, default=False)  # True for global notifications

    users = db.relationship('UserNotification', back_populates='notification')

    def __repr__(self):
        return f'<Notification {self.title}>'

# UserNotification association model
class UserNotification(BaseModel):
    __tablename__ = 'user_notifications'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.id'), primary_key=True)
    unread = db.Column(db.Boolean, default=True)
    user = db.relationship('User', back_populates='notifications')
    notification = db.relationship('Notification', back_populates='users')

    def __repr__(self):
        return f'<UserNotification user_id={self.user_id}, notification_id={self.notification_id}>'
