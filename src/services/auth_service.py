import os
import datetime
import stat
from werkzeug.security import generate_password_hash
from flask_login import login_user, logout_user, current_user
from src.config.app_config import db
from src.models import UserProfile, UserDashboardSettings
from src.services.messaging.email_service import send_smtp_email
from src.helper.template_utils import render_template_from_file
from src.helper.basic_info import ROOT_DIR
from src.services.common_helper import get_email_addresses
from src.config.app_config import get_app_info
from src.helper.logger import get_logger

logger = get_logger(__name__)

class AuthService:
    def __init__(self):
        self.app_info = get_app_info()

    def authenticate_and_login(self, username: str, password: str, remember_me: bool = False):
        user = UserProfile.query.filter(
            (UserProfile.username == username) | (UserProfile.email == username)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                return None, "Account is not active, Contact Admin"
            
            remember_duration = datetime.timedelta(days=7) if remember_me else datetime.timedelta(days=1)
            login_user(user, remember=remember_me, duration=remember_duration)
            logger.info(f"User {user.username} logged in")
            user.last_login = datetime.datetime.utcnow()
            user.save()

            self.send_login_alert(user)
            return user, None
        return None, "Invalid username or password"

    def send_login_alert(self, user):
        receiver_email = user.email
        admin_emails_with_alerts = get_email_addresses(
            user_level="admin", receive_email_alerts=True
        )
        if admin_emails_with_alerts:
            if receiver_email in admin_emails_with_alerts:
                admin_emails_with_alerts.remove(receiver_email)
            if admin_emails_with_alerts:
                context = {
                    "username": user.username,
                    "login_time": datetime.datetime.now(),
                    "title": self.app_info["title"]
                }
                login_alert_template = os.path.join(
                    ROOT_DIR, "src/templates/email_templates/admin_login_alert.html"
                )
                email_body = render_template_from_file(
                    login_alert_template, **context
                )
                send_smtp_email(
                    admin_emails_with_alerts,
                    "Login Alert",
                    email_body,
                    is_html=True,
                )
    @staticmethod
    def logout():
        logger.info(f"user {current_user.username} logged out")
        logout_user()

    def can_signup(self):
        total_users = UserProfile.fetch_total_count()
        max_users_allowed = self.app_info.get("max_users_allowed")
        if max_users_allowed is not None and total_users >= max_users_allowed:
            logger.error(
                f"Cannot create more users. You have reached the maximum limit of {max_users_allowed} users."
            )
            return False, max_users_allowed
        return True, None

    def create_user(self, form_data):
        first_name = form_data["first_name"]
        last_name = form_data["last_name"]
        username = form_data["username"]
        email = form_data["email"]
        password = form_data["password"]
        confirm_password = form_data["confirm_password"]
        user_level = form_data.get("user_level", "user")
        receive_email_alerts = "receive_email_alerts" in form_data
        profession = form_data.get("profession", None)

        if password != confirm_password:
            return None, "Passwords do not match"

        existing_user = UserProfile.query.filter(
            (UserProfile.username == username) | (UserProfile.email == email)
        ).first()
        if existing_user:
            return None, "Username or email already exists"

        hashed_password = generate_password_hash(password)
        new_user = UserProfile(
            first_name=first_name, # type: ignore
            last_name=last_name, # type: ignore
            username=username, # type: ignore
            email=email, # type: ignore
            password=hashed_password, # type: ignore
            user_level=user_level, # type: ignore
            receive_email_alerts=receive_email_alerts, # type: ignore
            profession=profession, # type: ignore
        )

        db.session.add(new_user)
        db.session.commit()

        self.send_new_user_alert(new_user)
        self.send_welcome_email(new_user)

        db.session.add(UserDashboardSettings(user_id=new_user.id)) # type: ignore
        db.session.commit()
        logger.info(f"New user {new_user.username} created")
        return new_user, None

    @staticmethod
    def send_new_user_alert(user):
        admin_emails_with_alerts = get_email_addresses(
            user_level="admin", receive_email_alerts=True
        )
        if admin_emails_with_alerts:
            subject = "New User Alert"
            context = {
                "username": user.username,
                "email": user.email,
                "registration_time": datetime.datetime.now(),
                "user_level": user.user_level,
            }
            new_user_alert_template = os.path.join(
                ROOT_DIR, "src/templates/email_templates/new_user_alert.html"
            )
            email_body = render_template_from_file(new_user_alert_template, **context)
            send_smtp_email(admin_emails_with_alerts, subject, email_body, is_html=True)

    def send_welcome_email(self, user):
        subject = f"Welcome to the {self.app_info['title']}"
        context = {
            "username": user.username,
            "email": user.email,
        }
        welcome_template = os.path.join(
            ROOT_DIR, "src/templates/email_templates/welcome.html"
        )
        email_body = render_template_from_file(welcome_template, **context)
        send_smtp_email(user.email, subject, email_body, is_html=True)