from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import LoginManager
from src.config.app_config import app
from src.services.auth_service import AuthService
from src.models import UserProfile

auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" # type: ignore

auth_service = AuthService()

@login_manager.user_loader
def load_user(user_id):
    return UserProfile.query.get(int(user_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        remember_me = request.form.get("remember_me") == "on"
        user, error = auth_service.authenticate_and_login(username, password, remember_me)
        if user:
            return redirect(url_for("dashboard"))
        else:
            flash(error or "An unknown error occurred", "danger")
            return redirect(url_for("login"))
    return render_template("auths/login.html")

@app.route("/logout")
def logout():
    auth_service.logout()
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    can_create, max_users_allowed = auth_service.can_signup()
    total_users = UserProfile.fetch_total_count()
    if not can_create:
        flash(
            f"Cannot create more users. You have reached the maximum limit of {max_users_allowed} users.",
            "danger",
        )
        return redirect(url_for("login"))

    if request.method == "POST":
        user, error = auth_service.create_user(request.form)
        if user:
            flash("Account created successfully, Contact Admin to activate your account", "success")
            return redirect(url_for("login"))
        else:
            flash(error or "An unknown error occurred", "danger")
            return redirect(url_for("signup"))

    return render_template("auths/signup.html", total_users=total_users)