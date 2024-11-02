from datetime import datetime

from src.models.base_model import BaseModel
from src.config import db


class UserArticle(BaseModel):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('UserProfile', backref='posts')
    comments = db.relationship('UserPostComment', backref='post', lazy=True)
    likes = db.relationship('UserPostLike', backref='post', lazy=True)

    def __repr__(self):
        return f"<Post {self.id} by User {self.user_id}>"


class UserPostComment(BaseModel):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('UserProfile', backref='UserPostComment')
    
    def __repr__(self):
        return f"<Comment {self.id} on Post {self.post_id}>"


class UserPostLike(BaseModel):
    __tablename__ = 'likes'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('UserProfile', backref='UserPostLike')
    
    def __repr__(self):
        return f"<Like {self.id} on Post {self.post_id}>"
