import datetime
from flask import Blueprint, jsonify
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

from src.backend.common.extensions import db
from src.backend.models.seat import Seat
from src.backend.models.booking import Booking, BookingStatus

seats_bp = Blueprint("seats", __name__)
@seats_bp.route("/seats", methods=["GET"], strict_slashes=False)
def get_all_seats():
    """
    Restituisce tutti i posti con:
    - stato di prenotazione attuale
    - stato di occupazione reale (derivato)
    """
    try:
        now = datetime.datetime.now()

        results = db.session.query(
            Seat,
            Booking.status
        ).outerjoin(
            Booking,
            and_(
                Seat.id == Booking.seat_id,
                Booking.status.in_([
                    BookingStatus.PENDING_CHECKIN,
                    BookingStatus.CONFIRMED
                ]),
                Booking.start_time <= now,
                Booking.end_time >= now
            )
        ).all()

        response = []
        for seat, booking_status in results:
            response.append({
                "seat_id": seat.id,
                "room_id": seat.room_id,
                "active": seat.is_active,
                "booking_status": booking_status if booking_status else None,
                "real_occupancy": seat.is_occupied  # campo derivato
            })

        return jsonify(response), 200

    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
@seats_bp.route("/seats/<int:seat_id>", methods=["GET"])
def get_single_seat(seat_id):
    try:
        seat = Seat.query.get(seat_id)
        if not seat:
            return jsonify({"error": "Seat not found"}), 404

        return jsonify({
            "seat_id": seat.id,
            "room_id": seat.room_id,
            "active": seat.is_active,
            "real_occupancy": seat.is_occupied
        }), 200

    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
