from datetime import datetime
from flask import request, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from src.backend.common.extensions import db
from sqlalchemy import func
from src.backend.common.logger import logger
from src.backend.models import TemperatureReading, Seat, Booking
from src.backend.models.booking import BookingStatus

temperature_bp = Blueprint("temperatures", __name__)
# Parametri di comfort (costanti di progetto)
COMFORT_TEMP = 2.0
TOLERANCE = 2.0

@temperature_bp.route("/temperatures")
class TemperatureIngest(MethodView):

    def post(self):
        data = request.get_json()

        try:
            room_id = int(data["room_id"])
            temperature = float(data["temperature"])
            now = datetime.utcnow()

            # salva lettura (assume TemperatureReading ha campi room_id, temperature, timestamp/created_at)
            reading = TemperatureReading(
                room_id=room_id,
                temperature=temperature
            )
            db.session.add(reading)
            db.session.commit()

            # ---- verifica prenotazione CONFIRMED attiva per la stanza ----
            booking_active = db.session.query(Booking).join(Seat).filter(
                Seat.room_id == room_id,
                Booking.status == BookingStatus.CONFIRMED
            ).first()
            logger.info(f"booking_active valore {booking_active}")
            # ---- verifica presenza fisica tramite seat.is_occupied ----
            #seats = Seat.query.filter_by(room_id=room_id).all()
            #presence = any([s.is_occupied for s in seats])

            # Se non c'è prenotazione valida o non c'è presenza => tutto OFF
            if not booking_active: #or not presence:
                hvac_action = "off"
                lights = False
            else:
                # calcolo HVAC in base alla temperatura
                if temperature > COMFORT_TEMP + TOLERANCE:
                    hvac_action = "cool"
                elif temperature < COMFORT_TEMP - TOLERANCE:
                    hvac_action = "heat"
                else:
                    hvac_action = "off"
                lights = True

            response = {
                "room_id": room_id,
                "hvac": hvac_action,
                "lights": lights
            }
            return jsonify(response), 200

        except Exception as e:
            db.session.rollback()
            logger.exception("Error processing temperature input")
            return jsonify({"error": str(e)}), 500

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
            logger.error(f"Error fetching temperature stats: {e}")
            return {"error": str(e)}, 500
