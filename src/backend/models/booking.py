from src.backend.common.extensions import db
class BookingStatus(str):
    PENDING_CHECKIN = "pending_checkin"
    CONFIRMED = "confirmed"  # durante la fascia oraria, seat occupato
    COMPLETED = "completed"

class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey("users.id", ondelete="CASCADE"),nullable=False )

    seat_id = db.Column(db.Integer,db.ForeignKey("seats.id", ondelete="CASCADE"),nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String, nullable=False, default=BookingStatus.PENDING_CHECKIN)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user = db.relationship('User', back_populates='bookings')
    seat = db.relationship('Seat', back_populates='bookings')

    def __repr__(self):
        return f"<Booking ID {self.id} - Status {self.status}>"
