# cython: language_level=3
import os
import datetime
from flask import render_template, redirect, url_for, request, blueprints, flash
from flask_login import LoginManager, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash

from services.messaging.email_service import send_smtp_email
from src.config.app_config import app, db
from src.models import (
    UserProfile,
    UserDashboardSettings,
)
from src.helper.template_utils import render_template_from_file, ROOT_DIR
from src.routes.helper.common_helper import get_email_addresses
from src.config.app_config import get_app_info
from src.helper.logger import get_logger
logger = get_logger(__name__)

auth_bp = blueprints.Blueprint("auth", __name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" # type: ignore

@login_manager.user_loader
def load_user(user_id):
    return UserProfile.query.get(int(user_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        remember_me = request.form.get("remember_me") == "on"  # TODO: Implement remember me

        user = UserProfile.query.filter(
            (UserProfile.username == username) | (UserProfile.email == username)
        ).first()
        if user and user.check_password(password):

            if not user.is_active:
                flash("Account is not active, Contact Admin", "danger")
                return redirect(url_for("login"))
            
            login_user(user, remember=remember_me)
            logger.info(f"User {user.username} logged in")
 
            user.last_login = datetime.datetime.utcnow()
            user.save()

            if remember_me:
                login_manager.remember_cookie_duration = datetime.timedelta(days=7) # type: ignore
            else: 
                login_manager.remember_cookie_duration = datetime.timedelta(days=1) # type: ignore

            receiver_email = current_user.email
            admin_emails_with_alerts = get_email_addresses(
                user_level="admin", receive_email_alerts=True
            )
            if admin_emails_with_alerts:
                if receiver_email in admin_emails_with_alerts:
                    admin_emails_with_alerts.remove(receiver_email)
                if admin_emails_with_alerts:
                    context = {
                        "username": current_user.username,
                        "login_time": datetime.datetime.now(),
                        "title": get_app_info()["title"]
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

            return redirect(url_for("dashboard"))
        flash("Invalid username or password", "danger")
    return render_template("auths/login.html")


@app.route("/logout")
def logout():
    logger.info(f"user {current_user.username} logged out")
    logout_user()

    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    total_users = UserProfile.fetch_total_count()
    max_users_allowed = get_app_info().get("max_users_allowed")

    if max_users_allowed is not None and total_users >= max_users_allowed:
        flash(
            f"Cannot create more users. You have reached the maximum limit of {max_users_allowed} users.",
            "danger",
        )
        logger.error(
            f"Cannot create more users. You have reached the maximum limit of {max_users_allowed} users."
        )

        return redirect(url_for("login"))

    if request.method == "POST":

        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        user_level = request.form.get(
            "user_level", "user"
        )
        receive_email_alerts = (
            "receive_email_alerts" in request.form
        )  # Checkbox is either checked or not
        profession = request.form.get("profession", None)

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("signup"))

        existing_user = UserProfile.query.filter(
            (UserProfile.username == username) | (UserProfile.email == email)
        ).first()
        if existing_user:
            flash("Username or email already exists")
            return redirect(url_for("signup"))

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

        # Get Admin Emails with Alerts Enabled:
        admin_emails_with_alerts = get_email_addresses(
            user_level="admin", receive_email_alerts=True
        )
        if admin_emails_with_alerts:
            subject = "New User Alert"
            context = {
                "username": new_user.username,
                "email": new_user.email,
                "registration_time": datetime.datetime.now(),
                "user_level": new_user.user_level,
            }
            new_user_alert_template = os.path.join(
                ROOT_DIR, "src/templates/email_templates/new_user_alert.html"
            )
            email_body = render_template_from_file(new_user_alert_template, **context)
            send_smtp_email(admin_emails_with_alerts, subject, email_body, is_html=True)

        # Send email to the new user
        subject = f"Welcome to the {get_app_info()['title']}"
        context = {
            "username": new_user.username,
            "email": new_user.email,
        }
        welcome_template = os.path.join(
            ROOT_DIR, "src/templates/email_templates/welcome.html"
        )
        email_body = render_template_from_file(welcome_template, **context)
        send_smtp_email(email, subject, email_body, is_html=True)

        new_user.save()
        db.session.add(UserDashboardSettings(user_id=new_user.id)) # type: ignore
        db.session.commit()
        flash("Account created successfully, Contact Admin to activate your account", "success")
        logger.info(f"New user {new_user.username} created")
        return redirect(url_for("login"))

    return render_template("auths/signup.html", total_users=total_users)
