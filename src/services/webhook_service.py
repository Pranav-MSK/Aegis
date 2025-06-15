from src.models import NotificationSettings, GeneralSettings
from typing import Tuple


def get_settings_data() -> Tuple[NotificationSettings, bool]:
    webhook_settings = NotificationSettings.query.first()
    if not webhook_settings:
        webhook_settings = NotificationSettings()  # Create a default instance if None
    general_settings = GeneralSettings.query.first()
    enable_alerts = general_settings.enable_alerts if general_settings else True
    return webhook_settings, enable_alerts


def update_webhook_settings(form: dict):
    # Parse booleans
    def parse_bool(key): return form.get(key) == "on"

    slack_webhook_url = form.get("slack_webhook_url")
    discord_webhook_url = form.get("discord_webhook_url")
    teams_webhook_url = form.get("teams_webhook_url")
    google_chat_webhook_url = form.get("google_chat_webhook_url")

    is_email_alert_enabled = parse_bool("is_email_alert_enabled")
    is_slack_alert_enabled = parse_bool("is_slack_alert_enabled")
    is_discord_alert_enabled = parse_bool("is_discord_alert_enabled")
    is_teams_alert_enabled = parse_bool("is_teams_alert_enabled")
    is_google_chat_alert_enabled = parse_bool("is_google_chat_alert_enabled")
    enable_alerts = parse_bool("enable_alerts")

    if not enable_alerts:
        is_email_alert_enabled = False
        is_slack_alert_enabled = False
        is_discord_alert_enabled = False
        is_teams_alert_enabled = False
        is_google_chat_alert_enabled = False

    # General settings
    general_settings = GeneralSettings.query.first()
    if not general_settings:
        general_settings = GeneralSettings(enable_alerts=enable_alerts) # type: ignore
    else:
        general_settings.enable_alerts = enable_alerts
    general_settings.save()

    # Webhook settings
    webhook_settings = NotificationSettings.query.first()
    if not webhook_settings:
        webhook_settings = NotificationSettings(
            slack_webhook_url=slack_webhook_url, # type: ignore
            discord_webhook_url=discord_webhook_url, # type: ignore
            teams_webhook_url=teams_webhook_url, # type: ignore
            google_chat_webhook_url=google_chat_webhook_url, # type: ignore
            is_email_alert_enabled=is_email_alert_enabled, # type: ignore
            is_slack_alert_enabled=is_slack_alert_enabled, # type: ignore
            is_discord_alert_enabled=is_discord_alert_enabled, # type: ignore
            is_teams_alert_enabled=is_teams_alert_enabled, # type: ignore
            is_google_chat_alert_enabled=is_google_chat_alert_enabled, # type: ignore
        )
    else:
        webhook_settings.slack_webhook_url = slack_webhook_url
        webhook_settings.discord_webhook_url = discord_webhook_url
        webhook_settings.teams_webhook_url = teams_webhook_url
        webhook_settings.google_chat_webhook_url = google_chat_webhook_url
        webhook_settings.is_email_alert_enabled = is_email_alert_enabled
        webhook_settings.is_slack_alert_enabled = is_slack_alert_enabled
        webhook_settings.is_discord_alert_enabled = is_discord_alert_enabled
        webhook_settings.is_teams_alert_enabled = is_teams_alert_enabled
        webhook_settings.is_google_chat_alert_enabled = is_google_chat_alert_enabled

    webhook_settings.save()
