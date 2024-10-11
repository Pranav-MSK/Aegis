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

    # Foreign key relations
    assigned_user = db.relationship('UserProfile', foreign_keys=[assigned_user_id], backref='assigned_alert_tickets')
    assigned_supervisor = db.relationship('UserProfile', foreign_keys=[assigned_supervisor_id], backref='supervised_alert_tickets')
    
    # Relationships to new models
    investigation_notes = db.relationship('InvestigationNote', backref='alert_ticket', lazy=True)
    reports = db.relationship('Report', backref='alert_ticket', lazy=True)
    alertlogs = db.relationship('AlertLog', backref='alert_ticket', lazy=True)


class AlertLog(BaseModel):
    __tablename__ = 'alert_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_ticket_id = db.Column(db.Integer, db.ForeignKey('alert_tickets.id'), nullable=False)
    log = db.Column(db.Text, nullable=False)  # Log message content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of log creation

# Investigation Note model to save individual investigation notes
class InvestigationNote(BaseModel):
    __tablename__ = 'investigation_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_ticket_id = db.Column(db.Integer, db.ForeignKey('alert_tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # User who added the note
    note = db.Column(db.Text, nullable=False)  # Investigation note content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of note creation

    # Foreign key relation
    user = db.relationship('UserProfile', backref='investigation_notes')


# Report model to save individual reports
class Report(BaseModel):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_ticket_id = db.Column(db.Integer, db.ForeignKey('alert_tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # User who submitted the report
    report = db.Column(db.Text, nullable=False)  # Report content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of report creation

    # Foreign key relation
    user = db.relationship('UserProfile', backref='reports')