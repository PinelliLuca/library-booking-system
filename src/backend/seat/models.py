from src.extensions import db
from sqlalchemy.sql import func

class Seat(db.Model):
    __tablename__ = "seats"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    row = db.Column(db.Integer, nullable=False)
    column = db.Column(db.Integer, nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)
    upd_user=db.Column(db.String, nullable=False)
    upd_datetime=db.Column(db.DateTime, nullable=False, default=func.now())

    def __repr__(self):
        return f"<Seat ID {self.id} ({self.row}, {self.column}) - {'Occupied' if self.is_occupied else 'Free'}>"
