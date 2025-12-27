from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required
from src.backend.models.seat_suggestion import SeatSuggestion

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
