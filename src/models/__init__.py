# cython: language_level=3
import os
import json
from flask_login import current_user
from werkzeug.security import generate_password_hash

from src.models.user_dashboard_settings import UserDashboardSettings
from src.models.application_general_settings import GeneralSettings
from src.models.smtp_configuration import SMTPSettings
from src.models.network_speed_test_result import NetworkSpeedTestResult
from src.models.user_profile import UserProfile, UserActivity, ActivityTable
from src.models.notification_settings import NotificationSettings, Notification, UserNotification
from src.models.alert_data_models import AlertTicket, InvestigationNote, Report, AlertLog, CustomFields
from src.models.graph_config import ChartConfiguration
from src.models.instance_metadata import InstanceMetadata
from src.models.user_post_model import UserArticle, UserPostComment, UserPostLike

from src.config import db, app
from src.logger import logger

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Context processor for injecting settings into templates
@app.context_processor
def inject_settings():
    if current_user.is_anonymous:
        user_dashboard_settings = UserDashboardSettings(user_id=0)
        general_settings = None
        return dict(
            user_dashboard_settings=user_dashboard_settings,
            general_settings=general_settings,
        )
    general_settings = GeneralSettings.query.first()
    user_dashboard_settings = UserDashboardSettings.query.filter_by(
        user_id=current_user.id
    ).first()  # Retrieve user-specific user_dashboard_settings from DB
  
    all_settings = dict(
        user_dashboard_settings=user_dashboard_settings,
        general_settings=general_settings,
    )
    return all_settings

if not os.path.exists(os.path.join(ROOT_DIR, "src/assets/.initialized")):
    with app.app_context():
        if not db.inspect(db.engine).has_table('users'):  # Use an important table to check existence
            logger.info("Creating tables")
            db.create_all()

            # create NotificationSettings
            if not NotificationSettings.query.first():
                NotificationSettings().save()

            activity_table_json = os.path.join(ROOT_DIR, "src/assets/activity_table.json")
            with open(activity_table_json, "r") as file:
                activity_table = json.load(file)
                for activity in activity_table:
                    
                    new_activity = ActivityTable(
                        activity_name=activity['activity_name'],
                        activity_point=activity['activity_point'],
                        activity_description=activity['activity_description']
                    )
                    new_activity.save()

            # Load predefined users from JSON file and add them to the database if not already present
            pre_defined_users_json = os.path.join(ROOT_DIR, "src/assets/predefine_user.json")
            initial_chart_configurations_json = os.path.join(ROOT_DIR, "src/assets/initial_chart_configurations.json")

            with open(initial_chart_configurations_json, "r") as file:
                initial_chart_configurations = json.load(file)


            try:
                with open(pre_defined_users_json, "r") as file:
                    pre_defined_users = json.load(file)

                for user_data in pre_defined_users:
                    if not UserProfile.query.filter_by(user_level=user_data["user_level"]).first():
                        hashed_password = generate_password_hash(user_data["password"])
                        user = UserProfile(
                            first_name=user_data["first_name"],
                            last_name=user_data["last_name"],
                            username=user_data["username"],
                            email=user_data["email"],
                            password=hashed_password,
                            user_level=user_data["user_level"],
                            receive_email_alerts=user_data["receive_email_alerts"],
                            profession=user_data["profession"],
                            is_active=user_data["is_active"],
                        )

                        user.save()
                        logger.info(f"Added predefined user: {user_data['username']}")

            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Error loading predefined users: {e}")

            # Initialize default dashboard settings for all users
            users = UserProfile.query.all()
            for user in users:
                if not user.dashboard_settings:
                    # Initialize settings with defaults if not set
                    db.session.add(UserDashboardSettings(user_id=user.id))
                    
                    for config in initial_chart_configurations:
                        # Skip adding production settings if not in production
                        if config['production'] == False and os.getenv("FLASK_ENV") == "production":
                            continue
                        new_chart_config = ChartConfiguration(
                            user_id=user.id,
                            metric_name=config['metric_name'],
                            title=config['title'],
                            xlabel=config['xlabel'],
                            ylabel=config['ylabel'],
                            chart_type=config['chart_type'],
                            tension=config.get('tension', 0.4),
                            point_radius=config.get('point_radius', 0),
                            point_hover_radius=config.get('point_hover_radius', 6),
                        )
                        new_chart_config.save()

                    db.session.commit()  # Commit once per user
                    logger.info(f"Initial settings data added for user ID: {user.id}")

            # Initialize default general settings if not present
            general_settings = GeneralSettings.query.first()
            if not general_settings:
                db.session.add(GeneralSettings())
                db.session.commit()
                logger.info("General settings initialized.")

            
        else:
            logger.info("Tables already exist. Skipping creation.")

    # Create a file to indicate that initialization has been done
    with open(os.path.join(ROOT_DIR, "src/assets/.initialized"), "w") as f:
        f.write("Initialization complete.")
