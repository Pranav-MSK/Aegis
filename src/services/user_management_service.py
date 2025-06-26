from datetime import datetime
import os
from flask_login import current_user
from werkzeug.security import generate_password_hash

from src.models import UserProfile, UserDashboardSettings, ActivityTable
from src.helper.template_utils import render_template_from_file
from src.helper.basic_info import ROOT_DIR
from src.infrastructure.messaging.email_service import send_smtp_email
from src.config.app_config import get_app_info, db
from src.services.common_helper import get_email_addresses
from src.helper.logger import get_logger

logger = get_logger(__name__)

class UserManagementService:
    def create_user(self, form_data):
        max_users_allowed = get_app_info().get("max_users_allowed")
        total_users = UserProfile.fetch_total_count()

        if max_users_allowed is not None and total_users >= max_users_allowed:
            message = f"Cannot create more users. Limit of {max_users_allowed} reached."
            logger.error(message)
            return False, message

        username = form_data['username']
        email = form_data['email']
        password = form_data['password']
        profession = form_data['profession']
        user_level = form_data.get('user_level', 'user')
        receive_email_alerts = form_data.get('receive_email_alerts', 'on') == 'on'
        assign_tickets = form_data.get('assign_tickets', 'on') == 'on'

        if UserProfile.query.filter_by(username=username).first() or UserProfile.query.filter_by(email=email).first():
            return False, 'Username or email already exists.'

        new_user = UserProfile(
            username=username, # type: ignore
            email=email, # type: ignore
            password=generate_password_hash(password), # type: ignore
            profession=profession, # type: ignore
            user_level=user_level, # type: ignore
            receive_email_alerts=receive_email_alerts, # type: ignore
            is_active=True, # type: ignore
            assign_tickets=assign_tickets # type: ignore
        )

        self.send_admin_alert_email(new_user)
        self.send_welcome_email(new_user)

        new_user.save()
        db.session.add(UserDashboardSettings(user_id=new_user.id)) # type: ignore
        new_user.save()

        return True, 'User created successfully!'

    def send_admin_alert_email(self, new_user):
        admin_emails = get_email_addresses(user_level='admin', receive_email_alerts=True)
        if not admin_emails:
            return
        subject = "New User Alert"
        context = {
            "current_user": current_user.username,
            "username": new_user.username,
            "email": new_user.email,
            "registration_time": datetime.now(),
            "user_level": new_user.user_level
        }
        template_path = os.path.join(ROOT_DIR, "src/templates/email_templates/new_user_create.html")
        body = render_template_from_file(template_path, **context)
        send_smtp_email(admin_emails, subject, body, is_html=True)

    def send_welcome_email(self, new_user):
        subject = f"Welcome to the {get_app_info()['title']}"
        context = {"username": new_user.username, "email": new_user.email}
        template_path = os.path.join(ROOT_DIR, "src/templates/email_templates/welcome.html")
        body = render_template_from_file(template_path, **context)
        send_smtp_email(new_user.email, subject, body, is_html=True)

    def update_user_profile(self, user, form_data):
        user.username = form_data['username']
        user.email = form_data['email']
        user.user_level = form_data['user_level']
        user.profession = form_data['profession']
        user.receive_email_alerts = 'receive_email_alerts' in form_data
        user.is_active = 'is_active' in form_data
        user.assign_tickets = 'assign_tickets' in form_data
        user.save()
        return True

    def delete_user(self, user):
        self.send_user_deletion_email(user)
        user.delete()
        return True

    def send_user_deletion_email(self, user):
        admin_emails = get_email_addresses(user_level='admin', receive_email_alerts=True)
        if not admin_emails:
            return
        subject = "User Deletion Alert"
        context = {
            "username": user.username,
            "deletion_time": datetime.now(),
            "current_user": current_user.username
        }
        template_path = os.path.join(ROOT_DIR, "src/templates/email_templates/deletion_email.html")
        body = render_template_from_file(template_path, **context)
        send_smtp_email(admin_emails, subject, body, is_html=True)

class ActivityService:
    def get_activities(self):
        return ActivityTable.query.all()

    def get_activity(self, activity_id):
        return ActivityTable.query.get_or_404(activity_id)

    def create_activity(self, data):
        new_activity = ActivityTable(
            activity_name=data["activity_name"], # type: ignore
            activity_point=data["activity_point"], # type: ignore
            activity_description=data["activity_description"] # type: ignore
        )
        new_activity.save()
        logger.info(f"Activity added: {new_activity} by {current_user.first_name} ({current_user.email})")
        return new_activity

    def update_activity(self, activity, data):
        activity.activity_name = data["activity_name"]
        activity.activity_point = data["activity_point"]
        activity.activity_description = data["activity_description"]
        activity.save()
        logger.info(f"Activity updated: {activity} by {current_user.first_name} ({current_user.email})")
        return activity

    def delete_activity(self, activity):
        activity.delete()
        logger.info(f"Activity deleted: {activity} by {current_user.first_name} ({current_user.email})")
        return True
