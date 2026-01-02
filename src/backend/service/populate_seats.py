from src.backend.models.room import Room
from src.backend.models.seat import Seat
from src.main import app
from src.backend.common.extensions import db
from src.backend.common.logger import logging

ROOM_SPECS = [
    {"name": "Room Alpha", "floor": 1, "sun_exposure": "north", "seat_count": 10},
    {"name": "Room Beta", "floor": 1, "sun_exposure": "south", "seat_count": 10},
    {"name": "Room Gamma", "floor": 2, "sun_exposure": "east", "seat_count": 5},
]

with app.app_context():
    created_rooms = []

    # Create rooms if they don't already exist
    for spec in ROOM_SPECS:
        room = Room.query.filter_by(name=spec["name"]).first()
        if not room:
            room = Room(name=spec["name"], floor=spec["floor"], sun_exposure=spec["sun_exposure"])
            db.session.add(room)
            db.session.flush()  # ensure room.id is available
            created_rooms.append(room.name)
    db.session.commit()

    # Populate seats for each room up to the desired count
    for spec in ROOM_SPECS:
        room = Room.query.filter_by(name=spec["name"]).first()
        if not room:
            continue
        existing = Seat.query.filter_by(room_id=room.id).count()
        to_create = spec["seat_count"] - existing
        for i in range(to_create):
            seat = Seat(is_occupied=False, upd_user="populate_seats_init", upd_datetime=db.func.now(), room_id=room.id)
            db.session.add(seat)
    db.session.commit()

    logging.info(f"Rooms created: {', '.join(created_rooms) if created_rooms else 'none (already existed)'}")
    for spec in ROOM_SPECS:
        room = Room.query.filter_by(name=spec["name"]).first()
        count = Seat.query.filter_by(room_id=room.id).count()
        logging.info(f"Room '{room.name}' - seats now: {count}")
