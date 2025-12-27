from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from src.backend.common.extensions import db

from src.backend.models import TemperatureReading

temperature_bp = Blueprint("temperatures", __name__)

@temperature_bp.route("/temperatures")
class TemperatureIngest(MethodView):

    def post(self):
        data = request.get_json()

        try:
            reading = TemperatureReading(
                room_id=data["room_id"],
                temperature=data["temperature"]
            )
            db.session.add(reading)
            db.session.commit()
            return {"message": "Temperature recorded"}, 201

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
