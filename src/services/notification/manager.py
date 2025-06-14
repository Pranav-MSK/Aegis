# cython: language_level=3
from typing import List, Dict, Any

from src.config.app_config import db
from src.helper.logger import get_logger
logger = get_logger(__name__)
from src.models import (
    Notification,
    SystemNotification)

# cython: language_level=3
from flask_login import current_user
from src.models import (
    AlertTicket,
    UserProfile,
    Notification,
    SystemNotification,
)
from src.schemas.discussion_board import UserNotification   

def generate_system_notification(user_notification_info: UserNotification, user_id=None):
 
    new_notification = Notification(
        type=user_notification_info.type, # type: ignore
        icon=user_notification_info.icon, # type: ignore
        title=user_notification_info.title, # type: ignore
        message=user_notification_info.message, # type: ignore
        is_global=user_notification_info.is_global, # type: ignore
    )

    new_notification.save()

    if new_notification.is_global:
        for user in UserProfile.query.all():
            user_notification = SystemNotification(
                user_id=user.id, # type: ignore
                notification_id=new_notification.id # type: ignore
            )
            user_notification.save()
    else:
        if not user_id:
            user_id = current_user.id
        user_notification = SystemNotification(
            user_id=user_id, # type: ignore
            notification_id=new_notification.id # type: ignore
        )
        user_notification.save()


def fetch_user_notifications(user_id: int, unread_only: bool = True, 
                             limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get notifications for a specific user with optional filtering and pagination.

    Args:
        user_id: The ID of the user
        unread_only: If True, only return unread notifications
        limit: Maximum number of notifications to return
        offset: Number of notifications to skip

    Returns:
        List of notification dictionaries
    """
    query = (
        db.session.query(Notification)
        .join(SystemNotification)
        .filter(SystemNotification.user_id == user_id)
    )

    if unread_only:
        query = query.filter(SystemNotification.unread == True)

    # Add global notifications that aren't already associated with the user
    global_notifications = query.union(
        db.session.query(Notification).filter(
            Notification.is_global == True,
            ~Notification.id.in_(
                db.session.query(SystemNotification.notification_id).filter(
                    SystemNotification.user_id == user_id
                )
            ),
        )
    )

    notifications = (
        global_notifications.order_by(Notification.time.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [notification.to_dict() for notification in notifications]
