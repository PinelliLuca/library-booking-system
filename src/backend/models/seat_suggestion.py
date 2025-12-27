from datetime import datetime

from src.backend.common.extensions import db

class SeatSuggestion(db.Model):
    __tablename__ = "seat_suggestions"

    id = db.Column(db.Integer, primary_key=True)
    seat_id = db.Column(db.Integer, db.ForeignKey("seats.id"))
    date = db.Column(db.Date)

    score = db.Column(db.Float)
    reason = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

