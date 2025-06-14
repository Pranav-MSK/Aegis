# cython: language_level=3
from datetime import datetime

from src.helper.logger import get_logger
logger = get_logger(__name__)
from src.models import (
    AlertTicket,
)
from src.config.app_config import get_app_info

def can_create_alert():
    try:
        current_date = datetime.now()
        first_date_of_month = current_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        if current_date.month == 12:
            next_month = current_date.replace(
                year=current_date.year + 1, month=1, day=1
            )
        else:
            next_month = current_date.replace(month=current_date.month + 1, day=1)

        total_alerts = AlertTicket.query.filter(
            AlertTicket.created_at >= first_date_of_month,
            AlertTicket.created_at < next_month,
        ).count()

        monthly_limit = get_app_info().get("monthly_alert_tickets_limit", 100)

        return total_alerts < monthly_limit

    except Exception as e:
        logger.error(f"Error checking monthly alerts: {str(e)}")
        return False  # Fail safe - don't create alert if there's an error
