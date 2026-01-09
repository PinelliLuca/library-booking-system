# controllers/seat_suggestions.py
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from sqlalchemy.exc import SQLAlchemyError

from src.backend.common.extensions import db
from src.backend.models.seat_suggestion import SeatSuggestion
from src.backend.models import Seat, Booking, Room, TemperatureReading, RoomEnergyState
from src.backend.models.user import User

import logging
logger = logging.getLogger("library-booking-system")

suggestion_bp = Blueprint("suggestions", __name__)

def _parse_date_hour(payload):
    """Helper: parse optional date and hour from payload or use now."""
    now = datetime.now()
    date_str = payload.get("date") if payload else None
    hour = payload.get("hour") if payload else None

    if date_str:
        try:
            target_date = datetime.fromisoformat(date_str).date()
        except Exception:
            raise ValueError("Invalid date format, expected YYYY-MM-DD")
    else:
        target_date = now.date()

    if hour is None:
        target_hour = now.hour
    else:
        try:
            target_hour = int(hour)
            if not (0 <= target_hour <= 23):
                raise ValueError("hour must be 0-23")
        except Exception:
            raise ValueError("Invalid hour value")
    return target_date, target_hour

def _sqlite_weekday_for_python_weekday(py_weekday):
    """SQLite '%w' returns 0=Sunday..6=Saturday; Python weekday() is 0=Mon..6=Sun.
       Map Python -> SQLite representation."""
    return (py_weekday + 1) % 7  # python Mon(0)->sqlite 1, Sun(6)->sqlite 0

@suggestion_bp.route("/seat-suggestions")
class SeatSuggestionList(MethodView):
    @jwt_required()
    def get(self):
        """
        GET /seat-suggestions?date=YYYY-MM-DD&top=10
        Returns suggestions for a given date (optional). If no date provided returns latest generated suggestions.
        """
        try:
            date_q = request.args.get("date")
            top = request.args.get("top", type=int)

            query = SeatSuggestion.query
            if date_q:
                try:
                    date_obj = datetime.fromisoformat(date_q).date()
                except Exception:
                    return {"error": "Invalid date format"}, 400
                query = query.filter(SeatSuggestion.date == date_obj)
            else:
                # if no date provided, pick latest date present
                latest = db.session.query(func.max(SeatSuggestion.date)).scalar()
                if latest:
                    query = query.filter(SeatSuggestion.date == latest)

            if top:
                query = query.order_by(SeatSuggestion.score.desc()).limit(top)
            else:
                query = query.order_by(SeatSuggestion.score.desc())

            results = query.all()

            out = [
                {
                    "seat_id": s.seat_id,
                    "score": s.score,
                    "reason": s.reason,
                    "is_recommended": getattr(s, "is_recommended", False)
                } for s in results
            ]
            return jsonify(out), 200

        except SQLAlchemyError as e:
            logger.error("DB error in SeatSuggestionList.get: %s", e)
            return {"error": "Database error", "details": str(e)}, 500
        except Exception as e:
            logger.exception("Unexpected error in SeatSuggestionList.get")
            return {"error": "Internal server error", "details": str(e)}, 500


@suggestion_bp.route("/seat-suggestions/generate")
class SeatSuggestionGenerate(MethodView):
    @jwt_required()
    def post(self):
        """
        POST /seat-suggestions/generate
        Body (optional):
        {
          "date": "YYYY-MM-DD",
          "hour": 10,
          "history_days": 90,
          "top_n": 10
        }

        Generates suggestions for a given date/hour (defaults: today/current hour),
        saves them to DB and marks top_n suggestions with is_recommended=True.
        """
        try:
            payload = request.get_json(silent=True) or {}
            target_date, target_hour = _parse_date_hour(payload)
            history_days = int(payload.get("history_days", 90))
            top_n = int(payload.get("top_n", 10))

            now = datetime.now()
            window_start = now - timedelta(days=history_days)

            seats = Seat.query.filter_by(is_active=True).all()

            # remove existing suggestions for the date
            db.session.query(SeatSuggestion).filter(SeatSuggestion.date == target_date).delete()

            suggestions = []
            # number of weeks (opportunities) in the history window
            weeks = max(1.0, history_days / 7.0)

            # compute sqlite weekday mapping for comparison (0=Sunday..6=Saturday)
            target_weekday_sqlite = _sqlite_weekday_for_python_weekday(target_date.weekday())

            for seat in seats:
                # Occupancy probability: count bookings for this seat with same weekday and hour in history
                try:
                    occ_count = db.session.query(func.count(Booking.id)).filter(
                        Booking.seat_id == seat.id,
                        Booking.start_time >= window_start,
                        func.strftime('%w', Booking.start_time) == str(target_weekday_sqlite),
                        func.strftime('%H', Booking.start_time) == f"{target_hour:02d}"
                    ).scalar() or 0
                except Exception:
                    # fallback - if DB flavor doesn't support strftime on datetime column, relax filters
                    occ_count = db.session.query(func.count(Booking.id)).filter(
                        Booking.seat_id == seat.id,
                        Booking.start_time >= window_start
                    ).scalar() or 0

                # occupancy probability: fraction of matching weeks with bookings
                occupancy_probability = min(1.0, float(occ_count) / weeks)

                # Comfort score: average recent temperature for the room (last 30 days)
                temp_window_days = 30
                temp_threshold = datetime.now() - timedelta(days=temp_window_days)
                avg_temp = db.session.query(func.avg(TemperatureReading.temperature)).filter(
                    TemperatureReading.room_id == seat.room_id,
                    TemperatureReading.timestamp >= temp_threshold
                ).scalar()
                if avg_temp is None:
                    comfort_score = 0.5
                else:
                    # seasonal ideal temperature
                    month = target_date.month
                    if month in (6, 7, 8):
                        ideal = 23.0
                    elif month in (12, 1, 2):
                        ideal = 21.0
                    else:
                        ideal = 22.0
                    comfort_score = max(0.0, 1.0 - (abs(avg_temp - ideal) / 10.0))

                    # adjust a bit for sun exposure in summer
                    room = Room.query.get(seat.room_id)
                    if room and room.sun_exposure and month in (6, 7, 8):
                        if room.sun_exposure.lower() in ("south", "west"):
                            comfort_score = max(0.0, comfort_score - 0.1)

                # Energy cost heuristic (use occupancy_probability + current room state)
                state = RoomEnergyState.query.filter_by(room_id=seat.room_id).first()
                if state and (state.lights_on or state.ac_on):
                    # room already active: lower marginal cost
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
                )
                # ensure attribute exists (if model extended with is_recommended)
                if hasattr(s, "is_recommended"):
                    s.is_recommended = False

                db.session.add(s)
                suggestions.append(s)

            db.session.flush()  # ensure IDs if needed

            # mark top_n as recommended
            if suggestions and hasattr(SeatSuggestion, "is_recommended"):
                top_sorted = sorted(suggestions, key=lambda x: x.score, reverse=True)[:top_n]
                for s in top_sorted:
                    s.is_recommended = True

            db.session.commit()

            out = sorted([
                {"seat_id": s.seat_id, "score": s.score, "reason": s.reason, "is_recommended": getattr(s, "is_recommended", False)}
                for s in suggestions
            ], key=lambda x: x["score"], reverse=True)

            return jsonify(out), 201

        except ValueError as e:
            logger.error("Bad request in generate: %s", e)
            return {"error": str(e)}, 400
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.exception("DB error in generate")
            return {"error": "Database error", "details": str(e)}, 500
        except Exception as e:
            db.session.rollback()
            logger.exception("Unexpected error in generate")
            return {"error": "Internal server error", "details": str(e)}, 500


@suggestion_bp.route("/seat-suggestions/recompute")
class SeatSuggestionRecompute(MethodView):
    @jwt_required()
    def post(self):
        """
        POST /seat-suggestions/recompute
        Admin-only forced recompute. Accepts same payload as /generate (optional).
        Returns count of generated suggestions.
        """
        try:
            username = get_jwt_identity()
            user = User.query.filter_by(username=username).first()
            if not user or user.role not in ("admin", "staff"):
                return {"error": "Forbidden"}, 403

            # Reuse generate logic by calling generate view function internally.
            payload = request.get_json(silent=True) or {}
            # We'll call the generate logic by constructing a request-like object:
            # For simplicity, directly forward to the POST implementation:
            generator = SeatSuggestionGenerate()
            # Monkey-call its post method (not ideal but acceptable here)
            resp, status = generator.post()
            if status == 201:
                generated = len(resp)
            else:
                generated = 0
            return {"message": "Recompute triggered", "generated": generated}, 200

        except SQLAlchemyError as e:
            logger.exception("DB error in recompute")
            return {"error": "Database error", "details": str(e)}, 500
        except Exception as e:
            logger.exception("Unexpected error in recompute")
            return {"error": "Internal server error", "details": str(e)}, 500


@suggestion_bp.route("/seat-suggestions/<int:seat_id>/explain")
class SeatSuggestionExplain(MethodView):
    @jwt_required()
    def get(self, seat_id):
        """
        GET /seat-suggestions/<seat_id>/explain?date=YYYY-MM-DD&hour=10
        Returns the detailed breakdown of the score for the seat (occupancy_probability, comfort_score, energy_cost).
        """
        try:
            date_q = request.args.get("date")
            hour_q = request.args.get("hour", type=int)

            payload = {}
            if date_q:
                payload["date"] = date_q
            if hour_q is not None:
                payload["hour"] = hour_q

            target_date, target_hour = _parse_date_hour(payload)

            # compute same metrics used in generation but for one seat
            history_days = 90
            window_start = datetime.now() - timedelta(days=history_days)
            target_weekday_sqlite = _sqlite_weekday_for_python_weekday(target_date.weekday())

            seat = Seat.query.get(seat_id)
            if not seat:
                return {"error": "Seat not found"}, 404

            occ_count = db.session.query(func.count(Booking.id)).filter(
                Booking.seat_id == seat.id,
                Booking.start_time >= window_start,
                func.strftime('%w', Booking.start_time) == str(target_weekday_sqlite),
                func.strftime('%H', Booking.start_time) == f"{target_hour:02d}"
            ).scalar() or 0

            weeks = max(1.0, history_days / 7.0)
            occupancy_probability = min(1.0, float(occ_count) / weeks)

            temp_threshold = datetime.now() - timedelta(days=30)
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
                room = Room.query.get(seat.room_id)
                if room and room.sun_exposure and month in (6, 7, 8):
                    if room.sun_exposure.lower() in ("south", "west"):
                        comfort_score = max(0.0, comfort_score - 0.1)

            state = RoomEnergyState.query.filter_by(room_id=seat.room_id).first()
            if state and (state.lights_on or state.ac_on):
                if occupancy_probability > 0.6:
                    energy_cost = 0.1
                else:
                    energy_cost = 0.4
            else:
                energy_cost = 0.8

            final_score = (occupancy_probability * 0.4) + (comfort_score * 0.3) - (energy_cost * 0.3)
            reason_text = f"occ={occupancy_probability:.2f},comfort={comfort_score:.2f},energy={energy_cost:.2f}"

            return jsonify({
                "seat_id": seat.id,
                "date": target_date.isoformat(),
                "hour": target_hour,
                "occupancy_probability": occupancy_probability,
                "comfort_score": comfort_score,
                "energy_cost": energy_cost,
                "final_score": final_score,
                "reason": reason_text
            }), 200

        except ValueError as e:
            return {"error": str(e)}, 400
        except SQLAlchemyError as e:
            logger.exception("DB error in explain")
            return {"error": "Database error", "details": str(e)}, 500
        except Exception as e:
            logger.exception("Unexpected error in explain")
            return {"error": "Internal server error", "details": str(e)}, 500
