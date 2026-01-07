from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from src.backend.common.extensions import db
from sqlalchemy import func
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
        
@temperature_bp.route("/temperatures/stats")
class TemperatureStats(MethodView):

    def get(self):
        try:
            avg_temp = db.session.query(func.avg(TemperatureReading.temperature)).scalar()
            max_temp = db.session.query(func.max(TemperatureReading.temperature)).scalar()
            min_temp = db.session.query(func.min(TemperatureReading.temperature)).scalar()

            return {
                "average_temperature": avg_temp,
                "max_temperature": max_temp,
                "min_temperature": min_temp
            }, 200

        except Exception as e:
            return {"error": str(e)}, 500
