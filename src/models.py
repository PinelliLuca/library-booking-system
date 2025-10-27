from main import db

class Seat(db.Model):
    __tablename__ = "seats"

    row = db.Column(db.Integer, primary_key=True)
    column = db.Column(db.Integer, primary_key=True)
    is_occupied = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Seat ({self.row}, {self.column}) - {'Occupied' if self.is_occupied else 'Free'}>"
