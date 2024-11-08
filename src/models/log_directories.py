# cython: language_level=3
from src.models.base_model import BaseModel
from src.config import db


class LogDirectory(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)

    def __init__(self, name, path):
        self.name = name
        self.path = path

    def to_dict(self):
        return {"name": self.name, "path": self.path}
