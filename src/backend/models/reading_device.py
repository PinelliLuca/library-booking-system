from datetime import datetime

from src.backend.common.extensions import db

class TemperatureReading(db.Model):
    __tablename__ = "temperature_readings"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"))

    temperature = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    room = db.relationship("Room", back_populates="temperatures")


class SeatOccupancyReading(db.Model):
    __tablename__ = "seat_occupancy_readings"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"))


    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
