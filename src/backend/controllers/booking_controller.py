import datetime
from flask import request, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

from src.backend.common.logger import logger
from src.backend.common.extensions import db
from src.backend.common.labels import BOOKING_FORCE_MOVE_BODY
from src.backend.models.booking import Booking, BookingStatus
from src.backend.models.user import User
from src.backend.models.seat import Seat
from src.backend.notification.mail import send_email

booking_bp = Blueprint("bookings", __name__, description="Booking management")

@booking_bp.route("/bookings", strict_slashes=False)
class BookingList(MethodView):

    @jwt_required()
    def get(self):
        """Return bookings. By default returns active/future bookings for all seats.

        Optional query params:
          - seat_id: filter by seat id
          - future_only: 'true' or 'false' (default 'true') -> filters bookings with end_time >= now

        Each booking includes 'username' and 'is_mine' boolean to let the client highlight user's bookings.
        """
        try:
            username = get_jwt_identity()
            user = User.query.filter_by(username=username).first()

            if not user:
                return {"error": "User not found"}, 404

            seat_id = request.args.get('seat_id', type=int)
            future_only = request.args.get('future_only', 'true').lower() in ('1', 'true', 'yes')

            now = datetime.datetime.now()
            q = Booking.query

            if seat_id:
                q = q.filter(Booking.seat_id == seat_id)

            if future_only:
                q = q.filter(Booking.end_time >= now)

            bookings = q.all()

            result = []
            for b in bookings:
                result.append({
                    "id": b.id,
                    "seat_id": b.seat_id,
                    "start_time": b.start_time.isoformat(),
                    "end_time": b.end_time.isoformat(),
                    "status": b.status,
                    "username": b.user.username if getattr(b, 'user', None) else None,
                    "is_mine": b.user_id == user.id
                })

            return result, 200

        except SQLAlchemyError as e:
            return {"error": "Database error", "details": str(e)}, 500
    @jwt_required()
    def post(self):
        """Create a new booking"""
        try:
            data = request.get_json()
            username = get_jwt_identity()
            user = User.query.filter_by(username=username).first()

            if not user:
                return {"error": "User not found"}, 404

            seat_id = data.get("seat_id")
            start_time = data.get("start_time")
            end_time = data.get("end_time")

            if not all([seat_id, start_time, end_time]):
                return {"error": "Missing required fields"}, 400

            start_time = datetime.datetime.fromisoformat(start_time)
            end_time = datetime.datetime.fromisoformat(end_time)

            if start_time >= end_time:
                return {"error": "Invalid time range"}, 400

            seat = Seat.query.get(seat_id)
            if not seat or not seat.is_active:
                return {"error": "Seat not available"}, 404

            #  overlap check
            overlapping = Booking.query.filter(
                Booking.seat_id == seat_id,
                Booking.status.in_([
                    BookingStatus.PENDING_CHECKIN,
                    BookingStatus.CONFIRMED
                ]),
                Booking.start_time < end_time,
                Booking.end_time > start_time
            ).first()

            if overlapping:
                return {"error": "Seat already booked in this time range"}, 409

            booking = Booking(
                user_id=user.id,
                seat_id=seat_id,
                start_time=start_time,
                end_time=end_time,
                status=BookingStatus.PENDING_CHECKIN
            )

            db.session.add(booking)
            db.session.commit()

            return {
                "message": "Booking created, waiting for check-in",
                "booking_id": booking.id
            }, 201

        except ValueError:
            return {"error": "Invalid datetime format"}, 400
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": "Database error", "details": str(e)}, 500
@booking_bp.route("/bookings/check-in")
class BookingCheckIn(MethodView):

    @jwt_required()
    def post(self):
        """Confirm booking via physical presence
        Accepts either `seat_id` (int) or `seat_identifier` (string UUID from QR code).
        """
        try:
            data = request.get_json()
            seat_id = data.get("seat_id")
            seat_identifier = data.get("seat_identifier")

            # resolve seat_identifier to seat_id if needed
            if not seat_id and seat_identifier:
                seat = Seat.query.filter_by(seat_identifier=seat_identifier).first()
                if seat:
                    seat_id = seat.id

            if not seat_id:
                return {"error": "Missing seat_id or seat_identifier"}, 400

            username = get_jwt_identity()
            user = User.query.filter_by(username=username).first()

            if not user:
                return {"error": "User not found"}, 404

            now = datetime.datetime.now()

            booking = Booking.query.filter(
                Booking.user_id == user.id,
                Booking.seat_id == seat_id,
                Booking.status == BookingStatus.PENDING_CHECKIN,
                Booking.start_time <= now,
                Booking.end_time >= now
            ).first()

            if not booking:
                return {"error": "No valid booking found"}, 404

            booking.status = BookingStatus.CONFIRMED
            db.session.commit()

            return {"message": "Check-in successful"}, 200

        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": "Database error", "details": str(e)}, 500
@booking_bp.route("/bookings/force-move")
class BookingForceMove(MethodView):

    #@admin_required
    def post(self):
        """
        Forza lo spostamento di una prenotazione su un altro posto
        """
        try:
            data = request.get_json()
            booking_id = data.get("booking_id")
            new_seat_id = data.get("new_seat_id")
            reason = data.get("reason")

            if not all([booking_id, new_seat_id, reason]):
                return {"error": "Missing required fields"}, 400

            booking = Booking.query.get(booking_id)
            if not booking:
                return {"error": "Booking not found"}, 404

            old_seat_id = booking.seat_id
            booking.seat_id = new_seat_id

            db.session.commit()

            # invio email
            user = booking.user
            send_email(
                subject="Spostamento prenotazione",
                body=BOOKING_FORCE_MOVE_BODY.format(
                    old_seat=old_seat_id,
                    new_seat=new_seat_id,
                    reason=reason
                ),
                recipients=[user.email]
            )

            return {
                "message": "Booking moved successfully",
                "old_seat_id": old_seat_id,
                "new_seat_id": new_seat_id
            }, 200

        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": "Database error", "details": str(e)}, 500


@booking_bp.route("/bookings/force-move")
class BookingForceMove(MethodView):
    def post(self):
        try:
            data = request.get_json()
            is_occupied = data.get("is_occupied")
            if not is_occupied:
                pass
                #se mi arriva un segnale che mi dice che la sedia è stata liberata
                # cerco l'utente seduto in quella prenotazione
                # invio una mail dove dico che a causa del fatto che si è alzato per troppo tempo il posto è stato liberato
                # cerco la prenotazione in booking e libero il posto
            return 201
        except Exception as e:
            logger.exception(e)
            raise
