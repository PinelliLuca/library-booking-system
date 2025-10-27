from main import db

class ParkingSpot(db.Model):
    __tablename__ = "parking_spots"

    id = db.Column(db.Integer, primary_key=True)
    row = db.Column(db.Integer, nullable=False)
    column = db.Column(db.Integer, nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Spot ({self.row}, {self.column}) - {'Occupied' if self.is_occupied else 'Free'}>"
