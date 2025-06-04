# cython: language_level=3
from datetime import datetime
from sqlalchemy import CheckConstraint

from src.models.base_model import BaseModel
from src.config import db


# Alert Ticket model to save the alert ticket data
class AlertTicket(BaseModel):
    """ 
    Alert ticket model to save the alert ticket data
    ---
    Attributes:

        - id: int
        - alert_name: str
        - instance: str
        - severity: str
        - summary: str
        - description: str
        - alert_status: str
        - ticket_status: str
        - system_username: str
        - system_hostname: str
        - fingerprint: str
        - runbook_url: str
        - created_at: datetime
        - updated_at: datetime
        - assigned_user_id: int
        - assigned_supervisor_id: int
        - investigation_notes: list
        - reports: list
        - alertlogs: list
        - customfields: list
    
    Methods:
        - to_dict: Return the dictionary representation of the model
        - serialize: Return the serialized representation of the model
    """

    __tablename__ = 'alert_tickets'
    __table_args__ = (
        db.Index('ix_alert_name', 'alert_name'),
        db.Index('ix_created_at', 'created_at'),
        CheckConstraint("ticket_status IN ('Open', 'In Progress', 'Resolved', 'Closed')", name='check_status'),
        CheckConstraint("severity IN ('critical', 'warning', 'info')", name='check_severity'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    alert_name = db.Column(db.String(255), nullable=False)  # Name of the alert triggered
    instance = db.Column(db.String(255), nullable=False)  # The instance that triggered the alert
    severity = db.Column(db.String(50), nullable=False)  # Severity of the alert (e.g., critical, warning)
    summary = db.Column(db.Text, nullable=False)  # Alert summary description
    description = db.Column(db.String(255), nullable=False)
    alert_status = db.Column(db.String(50), nullable=False)  # Alert status (firing, resolved)
    ticket_status = db.Column(db.String(50), nullable=False, default='Open')  # Ticket status (Open, In Progress, Resolved, Closed)

    system_username = db.Column(db.String(255), nullable=True)  # Username of the system that triggered the alert
    system_hostname = db.Column(db.String(255), nullable=True)  # Hostname of the system that triggered the alert
    fingerprint = db.Column(db.String(32), nullable=True)  # Fingerprint of the alert
    runbook_url = db.Column(db.String(255), nullable=True)  # URL to the runbook for the alert
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of ticket creation
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)  # Timestamp of last update
    
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # User investigating the alert
    assigned_supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Supervisor reviewing the ticket

    # Foreign key relations
    assigned_user = db.relationship('UserProfile', foreign_keys=[assigned_user_id], backref='assigned_alert_tickets')
    assigned_supervisor = db.relationship('UserProfile', foreign_keys=[assigned_supervisor_id], backref='supervised_alert_tickets')
    
    # Relationships to new models
    investigation_notes = db.relationship('InvestigationNote', backref='alert_ticket', lazy=True, cascade="all, delete-orphan")
    reports = db.relationship('Report', backref='alert_ticket', lazy=True, cascade="all, delete-orphan")
    alertlogs = db.relationship('AlertLog', backref='alert_ticket', lazy=True, cascade="all, delete-orphan")
    customfields = db.relationship('CustomFields', backref='alert_ticket', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'alert_name': self.alert_name,
            'instance': self.instance,
            'severity': self.severity,
            'summary': self.summary,
            'description': self.description,
            'alert_status': self.alert_status,
            'ticket_status': self.ticket_status,
            'system_username': self.system_username,
            'system_hostname': self.system_hostname,
            'fingerprint': self.fingerprint,
            'runbook_url': self.runbook_url,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'assigned_user_id': self.assigned_user_id,
            'assigned_supervisor_id': self.assigned_supervisor_id,
            'investigation_notes': [note.to_dict() for note in self.investigation_notes],
            'reports': [report.to_dict() for report in self.reports],
            'alertlogs': [log.to_dict() for log in self.alertlogs],
            'customfields': [field.to_dict() for field in self.customfields]
        }

    def serialize(self):
        return {
            'id': self.id,
            'alert_name': self.alert_name,
            'instance': self.instance,
            'severity': self.severity,
            'summary': self.summary,
            'description': self.description,
            'alert_status': self.alert_status,
            'ticket_status': self.ticket_status,
            'system_username': self.system_username,
            'system_hostname': self.system_hostname,
            'fingerprint': self.fingerprint,
            'runbook_url': self.runbook_url,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'assigned_user_id': self.assigned_user_id,
            'assigned_supervisor_id': self.assigned_supervisor_id,
            'investigation_notes': [note.to_dict() for note in self.investigation_notes],
            'reports': [report.to_dict() for report in self.reports],
            'alertlogs': [log.to_dict() for log in self.alertlogs],
            'customfields': [field.to_dict() for field in self.customfields]
        }

class AlertLog(BaseModel):
    """
    Alert Log model to save individual alert logs for an alert ticket
    ---
    Attributes:
        - id: int
        - alert_ticket_id: int
        - log: str
        - created_at: datetime
    ---
    Methods:
        - to_dict: Return the dictionary representation of the model

    """
    __tablename__ = 'alert_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_ticket_id = db.Column(db.Integer, db.ForeignKey('alert_tickets.id'), nullable=False)
    log = db.Column(db.Text, nullable=False)  # Log message content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of log creation

    def to_dict(self):
        return {
            'id': self.id,
            'alert_ticket_id': self.alert_ticket_id,
            'log': self.log,
            'created_at': self.created_at
        }

# Investigation Note model to save individual investigation notes
class InvestigationNote(BaseModel):
    """
    Investigation Note model to save individual investigation notes for an alert ticket

    Attributes:
        - id: int
        - alert_ticket_id: int
        - user_id: int
        - note: str
        - created_at: datetime
    
    Methods:
        - to_dict: Return the dictionary representation of the model
    """
    __tablename__ = 'investigation_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_ticket_id = db.Column(db.Integer, db.ForeignKey('alert_tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # User who added the note
    note = db.Column(db.Text, nullable=False)  # Investigation note content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of note creation

    # Foreign key relation
    user = db.relationship('UserProfile', backref='investigation_notes')

    def to_dict(self):
        return {
            'id': self.id,
            'alert_ticket_id': self.alert_ticket_id,
            'user_id': self.user_id,
            'note': self.note,
            'created_at': self.created_at
        }


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

    def to_dict(self):
        return {
            'id': self.id,
            'alert_ticket_id': self.alert_ticket_id,
            'user_id': self.user_id,
            'report': self.report,
            'created_at': self.created_at
        }


class CustomFields(BaseModel):
    """ 
    Custom field model to save remark fields for an alert ticket

    Attributes:
        - id: int
        - alert_ticket_id: int
        - field_name: str
        - field_value: str
        - created_at: datetime
    
    Methods:
        - to_dict: Return the dictionary representation of the model
    
    """


    __tablename__ = 'custom_fields'

    id = db.Column(db.Integer, primary_key=True)
    alert_ticket_id = db.Column(db.Integer, db.ForeignKey('alert_tickets.id'), nullable=False)
    field_name = db.Column(db.String(255), nullable=False)
    field_value = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of report creation

    def to_dict(self):
        return {
            'id': self.id,
            'alert_ticket_id': self.alert_ticket_id,
            'field_name': self.field_name,
            'field_value': self.field_value,
            'created_at': self.created_at
        }