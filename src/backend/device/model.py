from datetime import datetime

from src.backend.common.extensions import db

class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    device_type = db.Column(db.String(30))
    # seat_sensor | temperature_sensor | ac_controller | light_controller

    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=True)
    seat_id = db.Column(db.Integer, db.ForeignKey("seats.id"), nullable=True)

    last_seen = db.Column(db.DateTime)

    room = db.relationship("Room", back_populates="devices")

class SeatOccupancyReading(db.Model):
    __tablename__ = "seat_occupancy_readings"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"))

    weight_detected = db.Column(db.Boolean)
    proximity_detected = db.Column(db.Boolean)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
