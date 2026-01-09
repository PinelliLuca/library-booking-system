# controllers/seat_suggestions.py
from flask.views import MethodView
from flask_smorest import Blueprint
from flask import request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from src.backend.auth import admin_required
from src.backend.auth.auth import auth_required
from src.backend.common.extensions import db
from src.backend.common.logger import logger
from src.backend.models.seat_suggestion import SeatSuggestion
from src.backend.models import Seat, Booking, Room, TemperatureReading, RoomEnergyState
from src.backend.service.generate_suggestion_service import generate_suggestions_service

suggestion_bp = Blueprint("suggestions", __name__)

@suggestion_bp.route("/seat-suggestions")
class SeatSuggestionList(MethodView):
    @auth_required
    def get(self):
        """GET /seat-suggestions?date=&top=
        Returns suggestions for a date (or latest) optionally limited by top param.
        """
        try:
            date_q = request.args.get("date")
            top = request.args.get("top", type=int)
            query = SeatSuggestion.query
            if date_q:
                date_obj = datetime.fromisoformat(date_q).date()
                query = query.filter(SeatSuggestion.date == date_obj)
            else:
                latest = db.session.query(func.max(SeatSuggestion.date)).scalar()
                if latest:
                    query = query.filter(SeatSuggestion.date == latest)
            query = query.order_by(SeatSuggestion.score.desc())
            if top:
                query = query.limit(top)
            results = query.all()
            out = [{"seat_id": s.seat_id, "score": s.score, "reason": s.reason, "is_recommended": s.is_recommended} for s in results]
            return jsonify(out), 200
        except Exception as e:
            logger.exception("Error listing suggestions")
            return {"error":"Internal"}, 500

@suggestion_bp.route("/seat-suggestions/generate")
class SeatSuggestionGenerate(MethodView):
    @auth_required
    @admin_required
    def post(self):
        """POST /seat-suggestions/generate (admin)
        Body optional: date, hour, history_days, top_n, recent_weight
        """
        try:
            payload = request.get_json(silent=True) or {}
            suggestions = generate_suggestions_service(payload)
            out = [{"seat_id": s.seat_id, "score": s.score, "reason": s.reason, "is_recommended": s.is_recommended} for s in suggestions]
            return jsonify(out), 201
        except ValueError as e:
            return {"error": str(e)}, 400
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.exception("DB error generate")
            return {"error":"DB error"}, 500
        except Exception as e:
            logger.exception("Unexpected error generate")
            return {"error":"Internal"}, 500

@suggestion_bp.route("/seat-suggestions/recompute")
class SeatSuggestionRecompute(MethodView):
    @auth_required
    @admin_required
    def post(self):
        """POST /seat-suggestions/recompute - admin: calls same service as generate"""
        try:
            payload = request.get_json(silent=True) or {}
            suggestions = generate_suggestions_service(payload)
            return {"message":"Recompute done", "generated": len(suggestions)}, 200
        except Exception as e:
            logger.exception("Recompute error")
            return {"error":"Internal"}, 500

@suggestion_bp.route("/seat-suggestions/<int:seat_id>/explain")
class SeatSuggestionExplain(MethodView):
    @auth_required
    def get(self, seat_id):
        """
        GET /seat-suggestions/<seat_id>/explain?date=&hour=
        Returns numeric breakdown for the seat.
        """
        try:
            date_q = request.args.get("date")
            hour_q = request.args.get("hour", type=int)
            payload = {}
            if date_q:
                payload["date"] = date_q
            if hour_q is not None:
                payload["hour"] = hour_q
            # reuse service but for single seat we replicate logic small-scale:
            target_date = datetime.fromisoformat(payload["date"]).date() if payload.get("date") else datetime.utcnow().date()
            target_hour = int(payload.get("hour", datetime.utcnow().hour))
            # compute occupancy recent/annual same as service but only for this seat
            recent_days = 90
            window_start_recent = datetime.utcnow() - timedelta(days=recent_days)
            window_start_annual = datetime.utcnow() - timedelta(days=365)
            target_weekday_sqlite = (target_date.weekday() + 1) % 7
            hh = f"{target_hour:02d}"

            seat = Seat.query.get(seat_id)
            if not seat:
                return {"error":"Seat not found"}, 404

            occ_recent = db.session.query(func.count(Booking.id)).filter(
                Booking.seat_id == seat.id,
                Booking.start_time >= window_start_recent,
                func.strftime('%w', Booking.start_time) == str(target_weekday_sqlite),
                func.strftime('%H', Booking.start_time) == hh
            ).scalar() or 0
            prob_recent = min(1.0, float(occ_recent) / max(1.0, recent_days/7.0))

            occ_annual = db.session.query(func.count(Booking.id)).filter(
                Booking.seat_id == seat.id,
                Booking.start_time >= window_start_annual,
                func.strftime('%w', Booking.start_time) == str(target_weekday_sqlite),
                func.strftime('%H', Booking.start_time) == hh
            ).scalar() or 0
            prob_annual = min(1.0, float(occ_annual) / 52.0)

            recent_weight = 0.7
            occupancy_probability = recent_weight*prob_recent + (1-recent_weight)*prob_annual

            # comfort
            temp_threshold = datetime.utcnow() - timedelta(days=30)
            avg_temp = db.session.query(func.avg(TemperatureReading.temperature)).filter(
                TemperatureReading.room_id == seat.room_id,
                TemperatureReading.timestamp >= temp_threshold
            ).scalar()
            if avg_temp is None:
                comfort_score = 0.5
            else:
                month = target_date.month
                if month in (6,7,8):
                    ideal = 23.0
                elif month in (12,1,2):
                    ideal = 21.0
                else:
                    ideal = 22.0
                comfort_score = max(0.0, 1.0 - (abs(avg_temp - ideal)/10.0))
                room = Room.query.get(seat.room_id)
                if room and room.sun_exposure:
                    exposure_penalty = {"south":0.15,"west":0.10,"east":0.05,"north":0.0}
                    comfort_score = max(0.0, comfort_score - exposure_penalty.get(room.sun_exposure.lower(),0.0))

            state = RoomEnergyState.query.filter_by(room_id=seat.room_id).first()
            if state and (state.lights_on or state.ac_on):
                energy_cost = 0.1 if occupancy_probability>0.6 else 0.4
            else:
                energy_cost = 0.8

            final_score = (occupancy_probability*0.4)+(comfort_score*0.3)-(energy_cost*0.3)
            reason = f"occ={occupancy_probability:.2f},comfort={comfort_score:.2f},energy={energy_cost:.2f}"
            return jsonify({
                "seat_id": seat.id,
                "date": target_date.isoformat(),
                "hour": target_hour,
                "occupancy_probability": occupancy_probability,
                "comfort_score": comfort_score,
                "energy_cost": energy_cost,
                "final_score": final_score,
                "reason": reason
            }), 200

        except Exception as e:
            logger.exception("Error explain")
            return {"error":"Internal"}, 500
