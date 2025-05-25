# cython: language_level=3
from datetime import datetime
import hashlib
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from humanize import naturaltime

from src.config import db
from src.models.base_model import BaseModel


class UserProfile(BaseModel, UserMixin):
    """
    User profile model for the application
    ---
    Attributes:
        - id: int
        - username: the username
        - email: the email
        - password: the password
        - user_level: the user level
        - receive_email_alerts: if the user receives email alerts
        - profession: the profession of the user

    Methods:
        - get_by_username: Get user profile by username
        - get_by_email: Get user profile by email
        - get_by_id: Get user profile by ID
        - get_all: Get all user profiles
        - check_password: Check the password
        - get_profile_picture_url: Get the profile picture URL

    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    username = db.Column(db.String(50), index=True, unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    user_level = db.Column(db.String(10), nullable=False, default='user')
    receive_email_alerts = db.Column(db.Boolean, default=False)
    profession = db.Column(db.String(50), nullable=True)
    password_last_changed = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # New field
    last_login = db.Column(db.DateTime, nullable=True)
    date_joined = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)
    user_points = db.Column(db.Integer, default=0)
    assign_tickets = db.Column(db.Boolean, default=False)

    # Backref renamed to avoid conflict
    dashboard_settings = db.relationship('UserDashboardSettings', backref='user', uselist=False)

    def __repr__(self):
        return f"<UserProfile {self.username}>"
    
    @staticmethod
    def get_by_username(username):
        return UserProfile.query.filter_by(username=username).first()
    
    @staticmethod
    def get_by_email(email):
        return UserProfile.query.filter_by(email=email).first()
    
    # @staticmethod
    # def get_by_id(id):
    #     return UserProfile.query.get(id)
    
    # @staticmethod
    # def get_all():
    #     return UserProfile.query.all()
    
    # check_hashed_password
    def check_password(self, password):
        return check_password_hash(self.password, password)
    

    def get_profile_picture_url(self, size=200):
        # Create an MD5 hash of the email address
        email_hash = hashlib.md5(self.email.strip().lower().encode('utf-8')).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"
    
class UserActivity(BaseModel):
    """
    User activity model for the application

    Attributes:
        - id: int
        - user_id: int
        - type: str
        - text: str
        - created_at: datetime

    Methods:
        - to_dict: Convert user activity to a dictionary
    """
    __tablename__ = 'user_activity'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'ticket', 'badge', 'update'
    text = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'text': self.text,
            'time': naturaltime(datetime.utcnow() - self.created_at)
        }


class ActivityTable(BaseModel):
    """"
    Activity Table Model
    ---
    Attributes:
        - id: int
        - activity_name: str
        - activity_point: int
        - activity_description: str

    Methods:
        - __repr__: Return the string representation of the model
    """
    __tablename__ = 'activity_table'
    
    id = db.Column(db.Integer, primary_key=True)
    activity_name = db.Column(db.String(100), nullable=False, unique=True)
    activity_point = db.Column(db.Integer, nullable=False)
    activity_description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Award {self.activity_name}: {self.activity_point} points>'