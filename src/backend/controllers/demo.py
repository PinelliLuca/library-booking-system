# controllers/demo_populate.py
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from src.backend.common.extensions import db
from src.backend.common.logger import logger
from src.backend.models import Room, Seat, TemperatureReading, Booking, SeatSuggestion, User, RoomEnergyState
from src.backend.service.generate_suggestion_service import generate_suggestions_service
demo_bp = Blueprint("demo", __name__, url_prefix="/demo")

@demo_bp.route("/clear-all", methods=["POST"])
def clear_all():
    """
    Elimina dati demo in ordine coerente (attenzione alle FK):
    seat_suggestions -> bookings -> temperature_readings -> seats -> rooms -> room_energy_states
    """
    try:
        # delete dependent tables first
        db.session.query(SeatSuggestion).delete(synchronize_session=False)
        db.session.query(Booking).delete(synchronize_session=False)
        db.session.query(TemperatureReading).delete(synchronize_session=False)
        db.session.query(Seat).delete(synchronize_session=False)
        db.session.query(RoomEnergyState).delete(synchronize_session=False)
        db.session.query(Room).delete(synchronize_session=False)
        db.session.commit()
        return {"message":"Cleared demo data"}, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("Error clearing demo data")
        return {"error":"DB error"}, 500

@demo_bp.route("/populate-rooms-seats", methods=["POST"])
def populate_rooms_seats():
    """
    Crea 3 stanze:
      - cold (north)
      - medium (east)
      - hot (south)
    e 6 seats per stanza
    """
    try:
        # rooms
        r_cold = Room(name="Room Cold", floor=1, sun_exposure="north")
        r_med = Room(name="Room Medium", floor=1, sun_exposure="east")
        r_hot = Room(name="Room Hot", floor=2, sun_exposure="south")
        db.session.add_all([r_cold, r_med, r_hot])
        db.session.flush()  # get ids

        seats = []
        for r in (r_cold, r_med, r_hot):
            for i in range(1,7):  # 6 seats each
                s = Seat(code=f"{r.name[:3]}-{i}", room_id=r.id, is_active=True)
                seats.append(s)
        db.session.add_all(seats)
        db.session.commit()
        return {"message":"Rooms and seats created"}, 201
    except Exception as e:
        db.session.rollback()
        logger.exception("Error populate rooms/seats")
        return {"error":"Internal"}, 500

@demo_bp.route("/populate-temperatures", methods=["POST"])
def populate_temperatures():
    """
    Inserisce letture di temperatura per 60 giorni in modo coerente:
    - Room Cold: temps around 18-20
    - Room Medium: 21-23
    - Room Hot: 24-26
    """
    try:
        rooms = Room.query.all()
        now = datetime.utcnow()
        readings = []
        for r in rooms:
            for days_back in range(60):  # 60 daily samples
                ts = now - timedelta(days=days_back)
                if r.sun_exposure == "north":
                    temp = 18 + (days_back % 3)  # 18..20
                elif r.sun_exposure == "east":
                    temp = 21 + (days_back % 3)  # 21..23
                else:
                    temp = 24 + (days_back % 3)  # 24..26
                readings.append(TemperatureReading(room_id=r.id, temperature=temp, timestamp=ts))
        db.session.add_all(readings)
        db.session.commit()
        return {"message":"Temperatures populated"}, 201
    except Exception:
        db.session.rollback()
        logger.exception("Error populate temps")
        return {"error":"Internal"}, 500

@demo_bp.route("/populate-bookings", methods=["POST"])
def populate_bookings():
    """
    Crea storico booking nell'ultimo anno per le seats per mostrare occupancy patterns.
    Genera anche alcune prenotazioni future per demo.
    """
    try:
        seats = Seat.query.all()
        now = datetime.utcnow()
        bookings = []
        # historic weekly pattern: create bookings every Monday 10:00 for many weeks for some seats
        for s in seats:
            # make seat pattern: some seats are popular
            popularity = 1 if s.code.endswith("-1") or s.code.endswith("-2") else 0.4
            # create weekly bookings for past 30 weeks
            for w in range(1,30):
                start = (now - timedelta(weeks=w)).replace(hour=10, minute=0, second=0, microsecond=0)
                # randomly pick subset by popularity
                if (w % int(max(1, round(1/popularity))) == 0):
                    bookings.append(Booking(user_id=None, seat_id=s.id, start_time=start, end_time=start+timedelta(hours=2), status="confirmed"))
            # create some future bookings
            fstart = now + timedelta(days=1, hours=10)
            bookings.append(Booking(user_id=None, seat_id=s.id, start_time=fstart, end_time=fstart+timedelta(hours=2), status="pending_checkin"))
        db.session.add_all(bookings)
        db.session.commit()
        return {"message":"Bookings populated"}, 201
    except Exception:
        db.session.rollback()
        logger.exception("Error populate bookings")
        return {"error":"Internal"}, 500

@demo_bp.route("/run-scenario", methods=["POST"])
def run_scenario():
    """
    Esegue: genera suggerimenti (con default params) e restituisce top 10.
    """
    try:
        # call generation service via payload

        payload = {"history_days":90, "top_n":10}
        suggestions = generate_suggestions_service(payload)
        out = [{"seat_id": s.seat_id, "score": s.score, "is_recommended": s.is_recommended} for s in suggestions]
        return jsonify(sorted(out, key=lambda x: x["score"], reverse=True)[:10]), 200
    except Exception:
        logger.exception("Error run scenario")
        return {"error":"Internal"}, 500
