from main import app, db
from models import Seat

with app.app_context():
    for row in range(5):
        for column in range(5):
            seat = Seat(row=row, column=column, is_occupied=False)
            db.session.add(seat)
    db.session.commit()
    print("Matrice 5x5 di posti creata.")
