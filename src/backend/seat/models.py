import uuid
from src.backend.common.extensions import db

class Seat(db.Model):
    __tablename__ = "seats"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seat_identifier = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    is_occupied = db.Column(db.Boolean, default=False)
    upd_user=db.Column(db.String, nullable=False)
    upd_datetime=db.Column(db.DateTime, nullable=False)

    bookings = db.relationship('Booking', back_populates='seat', lazy=True)

    def __repr__(self):
        return f"<Seat ID {self.id} - {'Occupied' if self.is_occupied else 'Free'}>"
