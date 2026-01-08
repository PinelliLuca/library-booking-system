from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required
from src.backend.models.seat_suggestion import SeatSuggestion
from src.backend.models import Seat, Booking, Room, TemperatureReading, RoomEnergyState
from src.backend.common.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func

suggestion_bp = Blueprint("suggestions", __name__)

@suggestion_bp.route("/seat-suggestions")
class SeatSuggestionList(MethodView):

    @jwt_required()
    def get(self):
        suggestions = SeatSuggestion.query.order_by(
            SeatSuggestion.score.desc()
        ).all()

        return [
            {
                "seat_id": s.seat_id,
                "score": s.score,
                "reason": s.reason
            } for s in suggestions
        ], 200


@suggestion_bp.route("/seat-suggestions/generate")
class SeatSuggestionGenerate(MethodView):

    @jwt_required()
    def post(self):
        """Generate seat suggestions for a given date/hour (optional) and store them.

        Uses current date and hour.
        """
        # determine target date and hour
        now = datetime.now()
        target_date = now.date()
        target_hour = now.hour

        # analysis window for occupancy history
        history_days = 90
        window_start = datetime.now() - timedelta(days=history_days)

        seats = Seat.query.filter_by(is_active=True).all()

        # remove existing suggestions for the date
        db.session.query(SeatSuggestion).filter(SeatSuggestion.date == target_date).delete()

        suggestions = []
        weeks = max(1, history_days / 7.0)

        for seat in seats:
            # Occupancy probability: bookings for this seat with same weekday and hour
            occ_count = db.session.query(func.count(Booking.id)).filter(
                Booking.seat_id == seat.id,
                Booking.start_time >= window_start,
                func.extract('hour', Booking.start_time) == target_hour,
                func.extract('dow', Booking.start_time) == target_date.weekday()
            ).scalar() or 0

            occupancy_probability = min(1.0, (occ_count / max(1.0, weeks)))

            # Comfort score: based on recent average temperature for the room
            avg_temp = db.session.query(func.avg(TemperatureReading.temperature)).filter(
                TemperatureReading.room_id == seat.room_id,
                TemperatureReading.timestamp >= datetime.now() - timedelta(days=30)
            ).scalar()
            if avg_temp is None:
                # neutral comfort if no data
                comfort_score = 0.5
            else:
                ideal = 22.0
                comfort_score = max(0.0, 1.0 - (abs(avg_temp - ideal) / 10.0))

                # adjust for sun exposure in summer months
                month = target_date.month
                room = seat.room
                if room and room.sun_exposure and month in (6,7,8):
                    if room.sun_exposure.lower() in ('south', 'west'):
                        comfort_score = max(0.0, comfort_score - 0.1)

            # Energy cost: heuristic based on room energy state
            state = RoomEnergyState.query.filter_by(room_id=seat.room_id).first()
            if state and (state.lights_on or state.ac_on):
                energy_cost = 0.2
            else:
                energy_cost = 0.8

            # final score
            score = (occupancy_probability * 0.4) + (comfort_score * 0.3) - (energy_cost * 0.3)

            reason = f"occ={occupancy_probability:.2f},comfort={comfort_score:.2f},energy={energy_cost:.2f}"

            s = SeatSuggestion(
                seat_id=seat.id,
                date=target_date,
                score=score,
                reason=reason
            )
            db.session.add(s)
            suggestions.append(s)

        db.session.commit()

        # return top suggestions
        out = sorted([
            {"seat_id": s.seat_id, "score": s.score, "reason": s.reason} for s in suggestions
        ], key=lambda x: x["score"], reverse=True)

        return out, 201
