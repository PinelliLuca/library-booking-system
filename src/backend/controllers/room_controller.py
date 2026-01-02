from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required
from src.backend.models.room import Room

room_bp = Blueprint("rooms", __name__)

@room_bp.route("/rooms")
class RoomList(MethodView):

    @jwt_required()
    def get(self):
        rooms = Room.query.all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "floor": r.floor,
                "sun_exposure": r.sun_exposure
            } for r in rooms
        ], 200
