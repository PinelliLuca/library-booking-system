from src.backend.common.extensions import db
class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    floor = db.Column(db.Integer)

    sun_exposure = db.Column(db.String(20))
    # north, south, east, west (serve per il comfort)

    seats = db.relationship("Seat", back_populates="room")
    devices = db.relationship("Device", back_populates="room")
    temperatures = db.relationship("TemperatureReading", back_populates="room")
