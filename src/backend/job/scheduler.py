from datetime import datetime
from sqlalchemy import and_

from src.backend.common.logger import logger
from src.backend.common.extensions import db
from src.backend.common.labels import EMAIL_BOOKING_COMPLETED
from src.backend.models import Booking
from src.backend.models.booking import BookingStatus
from src.backend.notification.mail import send_email

def close_expired_bookings():
    now = datetime.now()
    logger.info(now)
    expired = Booking.query.filter(
        Booking.status == BookingStatus.CONFIRMED,
        Booking.end_time <= now
    ).all()
    logger.info(f"expired bookings: {expired}")
    for booking in expired:
        booking.status = BookingStatus.COMPLETED

        send_email(
            subject=EMAIL_BOOKING_COMPLETED["subject"],
            body=EMAIL_BOOKING_COMPLETED["body"].format(
                seat_id=booking.seat_id,
                end_time=booking.end_time
            ),
            recipients=[booking.user.email]
        )

    if expired:
        db.session.commit()
    logger.info(f"Closed {len(expired)} expired bookings.")