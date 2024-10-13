# cython: language_level=3
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

from src.models.base_model import BaseModel
from src.config import db


class GraphConfigs(BaseModel):

    __tablename__ = "graph_config"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    metrics_key = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., 'line', 'bar'
    y_label = db.Column(db.String(100), nullable=False)
    x_label = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    color_scheme = db.Column(db.String(100), nullable=True)
    data_source = db.Column(db.String(200), nullable=False)
    refresh_interval = db.Column(db.Integer, nullable=True)  # in seconds
    display_options = db.Column(JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Graph {self.title}>"