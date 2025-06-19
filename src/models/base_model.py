# cython: language_level=3
from src.config.app_config import db


class BaseModel(db.Model):
    """ 
    Base model for all models in the application
    ---
    Attributes:
        - id: int
        - created_at: datetime
        - updated_at: datetime
    ---
    Methods:
        - save: Save the model to the database
        - delete: Delete the model from the database
        - get_all: Get all records of the model
        - get_by_id: Get a record by ID
        - fetch_total_count: Fetch the total count of records
    """
    __abstract__ = True  # This ensures that SQLAlchemy doesn't create a table for this class

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def flush(self):
        db.session.flush()

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def get_by_id(cls, record_id):
        return cls.query.get(record_id)

    @classmethod
    def fetch_total_count(cls):
        return cls.query.count()