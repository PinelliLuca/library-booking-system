from datetime import datetime

from src.backend.common.extensions import db

class EnergyCommand(db.Model):
    __tablename__ = "energy_commands"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"))

    command_type = db.Column(db.String(30))
    # set_temp | lights_on | lights_off | ac_on | ac_off

    value = db.Column(db.Float, nullable=True)
    issued_by = db.Column(db.String(20))  # system | admin
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class RoomEnergyState(db.Model):
    __tablename__ = "room_energy_states"

    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), primary_key=True)

    lights_on = db.Column(db.Boolean, default=False)
    ac_on = db.Column(db.Boolean, default=False)
    target_temperature = db.Column(db.Float)

    last_updated = db.Column(db.DateTime)
