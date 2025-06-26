import random
import string
import hashlib
from datetime import datetime
from sqlalchemy import desc
from src.models import AlertTicket, UserProfile, UserActivity
from src.schemas import UserNotification
from src.services.notification.manager import generate_system_notification
from src.services.common_helper import log_activity
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash

class ProfileService:

    # avoid to create a new instance of this class
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ProfileService, cls).__new__(cls)
        return cls.instance

    @staticmethod
    def get_gravatar_url(email, size=200):
        email_hash = hashlib.md5(email.strip().lower().encode('utf-8'), usedforsecurity=False).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"

    @staticmethod
    def get_ticket_stats(user):
        user_assigned_tickets = AlertTicket.query.filter_by(assigned_user_id=user.id).all()
        supervisor_assigned_tickets = AlertTicket.query.filter_by(assigned_supervisor_id=user.id).all()
        return {
            'assigned': {
                'total': len(user_assigned_tickets),
                'open': len([t for t in user_assigned_tickets if t.ticket_status == 'Open']),
                'in_progress': len([t for t in user_assigned_tickets if t.ticket_status == 'In Progress']),
                'resolved': len([t for t in user_assigned_tickets if t.ticket_status == 'Resolved']),
                'closed': len([t for t in user_assigned_tickets if t.ticket_status == 'Closed']),
            },
            'supervised': {
                'total': len(supervisor_assigned_tickets),
                'open': len([t for t in supervisor_assigned_tickets if t.ticket_status == 'Open']),
                'in_progress': len([t for t in supervisor_assigned_tickets if t.ticket_status == 'In Progress']),
                'resolved': len([t for t in supervisor_assigned_tickets if t.ticket_status == 'Resolved']),
                'closed': len([t for t in supervisor_assigned_tickets if t.ticket_status == 'Closed']),
            }
        }
    
    @staticmethod
    def generate_random_password(length=12):
        password_characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(password_characters) for _ in range(length))

    @staticmethod
    def change_password(user, old_password, new_password, confirm_password):
        if not check_password_hash(user.password, old_password):
            return False, "Old password is incorrect."
        if new_password != confirm_password:
            return False, "New passwords do not match."
        user.password = generate_password_hash(new_password)
        user.last_updated = datetime.utcnow()
        user.password_last_changed = datetime.utcnow()
        user.save()
        notification_data = UserNotification(
            type="info",
            icon="info-circle",
            title="Password Changed",
            message="Your password was changed successfully.",
            is_global=False
        )
        generate_system_notification(notification_data)
        log_activity('edit', 'Password changed')
        return True, None

    @staticmethod
    def update_profile(user, form):
        user.first_name = form['first_name']
        user.last_name = form['last_name']
        user.username = form['username']
        user.email = form['email']
        user.profession = form['profession']
        user.receive_email_alerts = 'receive_email_alerts' in form
        user.assign_tickets = 'assign_tickets' in form
        user.last_updated = datetime.utcnow()
        user.save()
        notification_data = UserNotification(
            type="info",
            icon="info-circle",
            title="Profile Updated",
            message="Your profile was updated successfully.",
            is_global=False
        )
        generate_system_notification(notification_data)
        log_activity('edit', 'Profile updated')

    @staticmethod
    def delete_user(user):
        user.delete()
        log_activity('delete', 'User deleted their account')

    @staticmethod
    def get_recent_activities(user_id, page=1, per_page=10):
        user_profile = UserProfile.query.get(user_id)
        user_points = user_profile.user_points if user_profile else 0
        activities = (
            UserActivity.query.filter_by(user_id=user_id)
            .order_by(desc(UserActivity.created_at))
            .paginate(page=page, per_page=per_page)
        )
        return {
            "activities": [activity.to_dict() for activity in activities.items],
            "total": activities.total,
            "pages": activities.pages,
            "current_page": activities.page,
            "user_points": user_points,
        }