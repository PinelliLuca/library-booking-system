from src.backend.models.seat import Seat
from src.main import app
from src.backend.common.extensions import db
from src.backend.common.logger import logging

with app.app_context():
    for row in range(5):
        for column in range(5):
            seat = Seat(is_occupied=False, upd_user="populate_seats_init", upd_datetime=db.func.now())
            db.session.add(seat)
    db.session.commit()
    logging.info("Matrice 5x5 di posti creata.")
