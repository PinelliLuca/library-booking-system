from flask import request, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from src.backend.common.extensions import db
from src.backend.booking.models import Booking, BookingStatus
from src.backend.user.model.user import User
from src.backend.seat.models import Seat
from flask_jwt_extended import jwt_required, get_jwt_identity
import datetime

booking_bp = Blueprint("bookings", __name__, url_prefix="/bookings", description="Operations on bookings")

@booking_bp.route("/")
class BookingList(MethodView):
    @jwt_required()
    def get(self):
        """Get all bookings for the current user"""
        user_id = get_jwt_identity()
        bookings = Booking.query.filter_by(user_id=user_id).all()
        
        if not bookings:
            return jsonify([]), 200

        results = [
            {
                "id": b.id,
                "seat_id": b.seat_id,
                "start_time": b.start_time.isoformat(),
                "end_time": b.end_time.isoformat(),
                "status": b.status,
            }
            for b in bookings
        ]
        return jsonify(results), 200

    @jwt_required()
    def post(self):
        """Create a new booking"""
        data = request.get_json()
        user_id = get_jwt_identity()
        seat_id = data.get('seat_id')
        
        # Simple validation
        if not all([seat_id]):
            return jsonify({"message": "Missing seat_id"}), 400

        # Check if seat exists and is available
        seat = Seat.query.get(seat_id)
        if not seat:
            return jsonify({"message": "Seat not found"}), 404
        
        if seat.is_occupied:
            return jsonify({"message": "Seat is already occupied"}), 400

        # Create booking
        try:
            # For simplicity, we'll set start_time to now and end_time to 2 hours from now.
            start_time = datetime.datetime.utcnow()
            end_time = start_time + datetime.timedelta(hours=2)

            new_booking = Booking(
                user_id=user_id,
                seat_id=seat_id,
                start_time=start_time,
                end_time=end_time,
                status=BookingStatus.PENDING_CHECKIN
            )
            db.session.add(new_booking)
            
            db.session.commit()

            return jsonify({"message": "Booking created successfully, pending check-in", "booking_id": new_booking.id}), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Failed to create booking", "error": str(e)}), 500

@booking_bp.route("/check-in")
class CheckIn(MethodView):
    @jwt_required()
    def post(self):
        """Confirm a booking by checking in"""
        data = request.get_json()
        user_id = get_jwt_identity()
        seat_identifier = data.get('seat_identifier')

        if not seat_identifier:
            return jsonify({"message": "Missing seat_identifier"}), 400

        seat = Seat.query.filter_by(seat_identifier=seat_identifier).first()
        if not seat:
            return jsonify({"message": "Seat not found"}), 404

        booking = Booking.query.filter_by(
            user_id=user_id,
            seat_id=seat.id,
            status=BookingStatus.PENDING_CHECKIN
        ).first()

        if not booking:
            return jsonify({"message": "No pending booking found for this seat and user"}), 404

        # Check if the check-in is within the allowed time (15 minutes from booking start_time)
        # Note: For simplicity, we are not checking the 15 minute window in this iteration,
        # as the scheduled job will handle expired bookings.
        
        booking.status = BookingStatus.CONFIRMED
        db.session.commit()

        return jsonify({"message": "Check-in successful, booking confirmed"}), 200

