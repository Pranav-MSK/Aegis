# cython: language_level=3
from datetime import datetime

from src.models.base_model import BaseModel
from src.config import db


# Alert Ticket model to save the alert ticket data
class AlertTicket(BaseModel):
    __tablename__ = 'alert_tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_name = db.Column(db.String(255), nullable=False)  # Name of the alert triggered
    instance = db.Column(db.String(255), nullable=False)  # The instance that triggered the alert
    severity = db.Column(db.String(50), nullable=False)  # Severity of the alert (e.g., critical, warning)
    summary = db.Column(db.Text, nullable=False)  # Alert summary description
    description = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Open')  # Ticket status (Open, In Progress, Resolved, Closed)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of ticket creation
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)  # Timestamp of last update
    
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # User investigating the alert
    assigned_supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Supervisor reviewing the ticket
    investigation_notes = db.Column(db.Text, nullable=True)  # Investigation details/notes
    report = db.Column(db.Text, nullable=True)  # Final report submitted by the investigator

    # Foreign key relations
    assigned_user = db.relationship('UserProfile', foreign_keys=[assigned_user_id], backref='assigned_alert_tickets')
    assigned_supervisor = db.relationship('UserProfile', foreign_keys=[assigned_supervisor_id], backref='supervised_alert_tickets')
