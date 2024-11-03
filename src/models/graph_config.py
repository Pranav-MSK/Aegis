# cython: language_level=3
from datetime import datetime

from src.models.base_model import BaseModel
from src.config import db


class ChartConfiguration(BaseModel):
    """ 
    Chart configuration model for the application

    Attributes:
        - id: int
        - user_id: the user id
        - metric_name: the metric name
        - title: the title of the chart
        - xlabel: the x-axis label
        - ylabel: the y-axis label
        - chart_type: the type of chart
        - tension: the tension of the chart
        - point_radius: the point radius of the chart
        - point_hover_radius: the point hover radius of the chart
        - is_active: True if the chart is active
        - created_at: the created date of the chart
        - updated_at: the updated date of the chart
    
    Methods:
        - serialize: Serialize the chart configuration
        - to_dict: Convert the chart configuration to a dictionary
    """

    __tablename__ = "chart_configurations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    xlabel = db.Column(db.String(100), nullable=False)
    ylabel = db.Column(db.String(100), nullable=False)
    chart_type = db.Column(db.String(50), nullable=False)  # e.g., 'line', 'bar'
    tension = db.Column(db.Float, nullable=True, default=0.4)
    point_radius = db.Column(db.Integer, nullable=True, default=0)
    point_hover_radius = db.Column(db.Integer, nullable=True, default=6)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ChartConfiguration {self.title}>"

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric_name': self.metric_name,
            'title': self.title,
            'xlabel': self.xlabel,
            'ylabel': self.ylabel,
            'chart_type': self.chart_type,
            'tension': self.tension,
            'point_radius': self.point_radius,
            'point_hover_radius': self.point_hover_radius,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
    

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric_name': self.metric_name,
            'title': self.title,
            'xlabel': self.xlabel,
            'ylabel': self.ylabel,
            'chart_type': self.chart_type,
            'tension': self.tension,
            'point_radius': self.point_radius,
            'point_hover_radius': self.point_hover_radius,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }