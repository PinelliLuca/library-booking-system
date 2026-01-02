from datetime import datetime
from src.backend.common.extensions import db
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String,unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    role = db.Column(db.String(20), default="student")  # student | admin | staff
    # token = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ins_istance=db.Column(db.DateTime, default=db.func.current_timestamp())

    bookings = db.relationship('Booking', back_populates='user', lazy=True)
    tokens = db.relationship("UserToken", back_populates="user")