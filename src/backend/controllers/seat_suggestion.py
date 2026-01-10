from flask.views import MethodView
from flask_smorest import Blueprint
from flask import request, jsonify
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from src.backend.auth.admin_required import admin_required
from src.backend.auth.auth import auth_required
from src.backend.common.extensions import db
from src.backend.common.logger import logger
from src.backend.models.seat_suggestion import SeatSuggestion
from src.backend.service.generate_suggestion_service import _generate_suggestions_service, _parse_payload_date_hour

suggestion_bp = Blueprint("suggestions", __name__)


@suggestion_bp.route("/seat-suggestions")
class SeatSuggestionList(MethodView):
    @auth_required
    def get(self):
        """
        GET /seat-suggestions?date=YYYY-MM-DD&top=10
        Returns saved suggestions for a date (or latest) ordered by score.
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
            out = [{"seat_id": s.seat_id, "score": round(s.score, 3), "reason": s.reason, "is_recommended": s.is_recommended} for s in results]
            return jsonify(out), 200
        except Exception as e:
            logger.exception("Error listing suggestions")
            return {"error":"Internal"}, 500

@suggestion_bp.route("/seat-suggestions/generate")
class SeatSuggestionGenerate(MethodView):
    @auth_required
    @admin_required
    def post(self):
        """
        POST /seat-suggestions/generate
        Admin-only. Body optional: date, hour, history_days, top_n, recent_weight
        """
        try:
            payload = request.get_json(silent=True) or {}
            suggestions = _generate_suggestions_service(payload)
            out = [{"seat_id": s.seat_id, "score": round(s.score,3), "reason": s.reason, "is_recommended": s.is_recommended} for s in suggestions]
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
        """
        Admin-only forced recompute. Same params as /generate.
        Returns count generated.
        """
        try:
            payload = request.get_json(silent=True) or {}
            suggestions = _generate_suggestions_service(payload)
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
        Returns numeric breakdown for the seat (occupancy_probability, comfort_score, energy_cost).
        """
        try:
            date_q = request.args.get("date")
            hour_q = request.args.get("hour", type=int)
            payload = {}
            if date_q:
                payload["date"] = date_q
            if hour_q is not None:
                payload["hour"] = hour_q

            # reuse logic but compute only for the single seat (same algorithms)
            suggestions_sample = _generate_suggestions_service(payload)  # cheap enough for a single seat in demo
            # find seat in generated suggestions
            for s in suggestions_sample:
                if s.seat_id == seat_id:
                    return jsonify({
                        "seat_id": s.seat_id,
                        "date": s.date.isoformat(),
                        "score": round(s.score,3),
                        "reason": s.reason,
                        "is_recommended": s.is_recommended
                    }), 200
            return {"error":"Seat not found in generated suggestions"}, 404
        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            logger.exception("Error explain")
            return {"error":"Internal"}, 500
