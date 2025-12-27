from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from src.backend.common.extensions import db
from src.backend.models import SeatOccupancyReading

occupancy_bp = Blueprint("occupancy", __name__)

@occupancy_bp.route("/seat-occupancy")
class SeatOccupancyIngest(MethodView):

    def post(self):
        data = request.get_json()

        try:
            reading = SeatOccupancyReading(
                device_id=data["device_id"],
                weight_detected=data["weight"],
                proximity_detected=data["proximity"]
            )
            db.session.add(reading)
            db.session.commit()
            return {"message": "Occupancy reading saved"}, 201

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
