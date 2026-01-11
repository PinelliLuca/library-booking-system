from datetime import datetime
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from src.backend.common.logger import logger
from src.backend.common.extensions import db
from src.backend.models import (
    SeatOccupancyReading,
    Seat,
    Booking,
    User
)
from src.backend.common.labels import EMAIL_FORCE_RELEASE
from src.backend.models.booking import BookingStatus
from src.backend.notification.mail import send_email

occupancy_bp = Blueprint("occupancy", __name__)

@occupancy_bp.route("/seat-occupancy")
class SeatOccupancyIngest(MethodView):

    def post(self):
        data = request.get_json()
        now = datetime.now()

        try:
            device_id = data["device_id"]
            is_occupied = data["is_occupied"]
            seat = Seat.query.filter_by(id=device_id).first()
            if not seat:
                raise ValueError("Seat not found for device_id")
            # salva la lettura IoT
            seat.is_occupied = is_occupied
            logger.info(f"Occupancy seat: {seat}")
            # prenotazione attiva
            booking = Booking.query.filter(
                Booking.seat_id == device_id,
                Booking.status == BookingStatus.CONFIRMED,
                Booking.start_time <= now,
                Booking.end_time >= now
            ).first()
            logger.info(f"Occupancy booking: {booking}")
            # CASO 1: qualcuno si siede → confermo la prenotazione
            if is_occupied:
                if booking:
                    # già confermata, non faccio nulla
                    pass
                else:
                    # se esiste una prenotazione pending, la confermo
                    pending = Booking.query.filter(
                        Booking.seat_id == device_id,
                        Booking.status == BookingStatus.PENDING_CHECKIN,
                        Booking.start_time <= now,
                        Booking.end_time >= now
                    ).first()

                    if pending:
                        pending.status = BookingStatus.CONFIRMED

            # CASO 2: la sedia si libera → rilascio forzato
            else:
                if booking:
                    booking.status = BookingStatus.COMPLETED

                    user = User.query.get(booking.user_id)

                    send_email(
                        subject=EMAIL_FORCE_RELEASE["subject"],
                        body=EMAIL_FORCE_RELEASE["body"].format(
                            user_name=user.username,
                            seat_id=seat.id,
                            end_time=booking.end_time.strftime("%H:%M")
                        ),
                        recipients=[user.email]
                    )

            db.session.commit()
            logger.info("message: Occupancy processed")
            return {"message": "Occupancy processed"}, 201

        except Exception as e:
            db.session.rollback()
            logger.exception(e)
            return {"error": str(e)}, 500
