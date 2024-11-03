# cython: language_level=3
from datetime import datetime

from src.models.base_model import BaseModel
from src.config import db


class UserArticle(BaseModel):
    """  User Article Model 

    Attributes:
        - id: int
        - user_id: int
        - title: str
        - content: str
        - tags: str
        - is_deleted: bool
        - created_at: datetime
        - updated_at: datetime

    Methods:
        - __repr__: Return the string representation of the model
    """

    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(255), nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('UserProfile', backref='posts')
    comments = db.relationship('UserPostComment', backref='post', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('UserPostLike', backref='post', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Post {self.id} by User {self.user_id}>"

class UserPostComment(BaseModel):
    """ User Post Comment Model\
    
    Attributes:
        - id: int
        - post_id: int
        - user_id: int
        - content: str
        - created_at: datetime
        - updated_at: datetime


    Methods:
        - __repr__: Return the string representation of the model

    """

    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('UserProfile', backref='UserPostComment')

    def __repr__(self):
        return f"<Comment {self.id} on Post {self.post_id}>"


class UserPostLike(BaseModel):
    """
    User Post Like Model 

    Attributes:
        - id: int
        - post_id: int
        - user_id: int
        - created_at: datetime

    Methods:
        - __repr__: Return the string representation of the model
    """
    __tablename__ = 'likes'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('UserProfile', backref='UserPostLike')
    
    def __repr__(self):
        return f"<Like {self.id} on Post {self.post_id}>"


class UserSavedPost(BaseModel):
    """
    User Saved Post Model

    Attributes:
        - id: int
        - user_id: int
        - post_id: int
        - created_at: datetime

    Methods:
        - __repr__: Return the string representation of the
    
    Relationships:
        - user: User relationship
        - post: Post relationship
    """
    __tablename__ = 'saved_posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('UserProfile', backref='saved_posts')
    post = db.relationship('UserArticle', backref='saved_by')

    def __repr__(self):
        return f"<SavedPost user_id={self.user_id} post_id={self.post_id}>"


class UserPostReport(BaseModel):
    """
    User Post Report Model

    Attributes:
        - id: int
        - post_id: int
        - user_id: int
        - reason: str
        - created_at: datetime

    Methods:
        - __repr__: Return the string representation of the model
        
    """
    __tablename__ = 'post_reports'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    post = db.relationship('UserArticle', backref='reports')
    user = db.relationship('UserProfile', backref='post_reports')

    def __repr__(self):
        return f"<Report user_id={self.user_id} post_id={self.post_id}>"
