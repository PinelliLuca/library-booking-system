from datetime import datetime, timedelta
from sqlalchemy import func
from src.backend.common.extensions import db
from src.backend.models.seat_suggestion import SeatSuggestion
from src.backend.models import Seat, Booking, Room, TemperatureReading, RoomEnergyState


def generate_suggestions_service(payload: dict):
    """
    payload optional keys:
      - date: YYYY-MM-DD
      - hour: int 0-23
      - history_days: int (recent window in days)
      - top_n: int (how many to mark recommended)
      - recent_weight: float in [0,1] weight for recent window in combined occupancy prob
    Returns list of created SeatSuggestion objects (not JSON).
    """
    now = datetime.utcnow()
    target_date = None
    target_hour = None

    # parse payload
    if payload is None:
        payload = {}
    if payload.get("date"):
        target_date = datetime.fromisoformat(payload["date"]).date()
    else:
        target_date = now.date()
    target_hour = int(payload.get("hour", now.hour))

    history_days = int(payload.get("history_days", 90))
    top_n = int(payload.get("top_n", 10))
    recent_weight = float(payload.get("recent_weight", 0.7))  # weight for recent window vs annual

    # windows
    window_start_recent = now - timedelta(days=history_days)
    window_start_annual = now - timedelta(days=365)

    seats = Seat.query.filter_by(is_active=True).all()

    # delete existing suggestions for the date
    db.session.query(SeatSuggestion).filter(SeatSuggestion.date == target_date).delete(synchronize_session=False)

    suggestions = []
    # weeks normalization
    weeks_recent = max(1.0, history_days / 7.0)
    weeks_annual = max(1.0, 52.0)  # approx 52 weeks

    # map python weekday -> sqlite '%w' (0=Sunday..6=Saturday)
    target_weekday_sqlite = (target_date.weekday() + 1) % 7
    hh = f"{target_hour:02d}"

    for seat in seats:
        #  occupancy recent
        try:
            occ_recent = db.session.query(func.count(Booking.id)).filter(
                Booking.seat_id == seat.id,
                Booking.start_time >= window_start_recent,
                func.strftime('%w', Booking.start_time) == str(target_weekday_sqlite),
                func.strftime('%H', Booking.start_time) == hh
            ).scalar() or 0
        except Exception:
            # fallback: count bookings in recent window without weekday/hour precision
            occ_recent = db.session.query(func.count(Booking.id)).filter(
                Booking.seat_id == seat.id,
                Booking.start_time >= window_start_recent
            ).scalar() or 0

        prob_recent = min(1.0, float(occ_recent) / weeks_recent)

        #  occupancy annual
        try:
            occ_annual = db.session.query(func.count(Booking.id)).filter(
                Booking.seat_id == seat.id,
                Booking.start_time >= window_start_annual,
                func.strftime('%w', Booking.start_time) == str(target_weekday_sqlite),
                func.strftime('%H', Booking.start_time) == hh
            ).scalar() or 0
        except Exception:
            occ_annual = db.session.query(func.count(Booking.id)).filter(
                Booking.seat_id == seat.id,
                Booking.start_time >= window_start_annual
            ).scalar() or 0

        prob_annual = min(1.0, float(occ_annual) / weeks_annual)

        # blended occupancy probability
        occupancy_probability = recent_weight * prob_recent + (1 - recent_weight) * prob_annual

        #  comfort score (avg temp)
        temp_window_days = 30
        temp_threshold = now - timedelta(days=temp_window_days)
        avg_temp = db.session.query(func.avg(TemperatureReading.temperature)).filter(
            TemperatureReading.room_id == seat.room_id,
            TemperatureReading.timestamp >= temp_threshold
        ).scalar()
        if avg_temp is None:
            comfort_score = 0.5
        else:
            month = target_date.month
            if month in (6, 7, 8):
                ideal = 23.0
            elif month in (12, 1, 2):
                ideal = 21.0
            else:
                ideal = 22.0
            comfort_score = max(0.0, 1.0 - (abs(avg_temp - ideal) / 10.0))
            # exposure penalty more granular
            try:
                room = Room.query.get(seat.room_id)
                if room and room.sun_exposure:
                    exposure_penalty = {
                        "south": 0.15,
                        "west": 0.10,
                        "east": 0.05,
                        "north": 0.0
                    }
                    comfort_score = max(0.0, comfort_score - exposure_penalty.get(room.sun_exposure.lower(), 0.0))
            except Exception:
                pass

        #  energy cost heuristic
        state = RoomEnergyState.query.filter_by(room_id=seat.room_id).first()
        if state and (state.lights_on or state.ac_on):
            # room active -> lower marginal cost
            if occupancy_probability > 0.6:
                energy_cost = 0.1
            else:
                energy_cost = 0.4
        else:
            energy_cost = 0.8

        # final score
        score = (occupancy_probability * 0.4) + (comfort_score * 0.3) - (energy_cost * 0.3)

        reason = f"occ={occupancy_probability:.2f},comfort={comfort_score:.2f},energy={energy_cost:.2f}"

        s = SeatSuggestion(
            seat_id=seat.id,
            date=target_date,
            score=score,
            reason=reason,
            is_recommended=False
        )
        db.session.add(s)
        suggestions.append(s)

    db.session.flush()

    # mark top_n recommended
    top_n = int(payload.get("top_n", 10))
    top_sorted = sorted(suggestions, key=lambda x: x.score, reverse=True)[:top_n]
    for s in top_sorted:
        s.is_recommended = True

    db.session.commit()
    return suggestions
