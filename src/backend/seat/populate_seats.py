from src.backend.seat.models import Seat
from src.main import app, db
# from src.extensions import db

with app.app_context():
    for row in range(5):
        for column in range(5):
            seat = Seat(row=row, column=column, is_occupied=False, upd_user="populate_seats")
            db.session.add(seat)
    db.session.commit()
    print("Matrice 5x5 di posti creata.")
