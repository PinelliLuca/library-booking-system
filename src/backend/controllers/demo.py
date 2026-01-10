import random
from flask import Blueprint, request
from datetime import datetime, timedelta
from flask.views import MethodView
from src.backend.common.extensions import db
from src.backend.models import Room, Seat, TemperatureReading, Booking, SeatSuggestion, User, RoomEnergyState
from src.backend.models.booking import BookingStatus
from src.backend.service.generate_suggestion_service import _generate_suggestions_service
from src.backend.common.logger import logger
demo_bp = Blueprint("demo", __name__, description="Demo utilities for exam and system showcase")

# CLEAR ALL

@demo_bp.route("/demo/clear-all")
class DemoClearAll(MethodView):
    def post(self):
        """
        Elimina tutti i dati di demo rispettando FK.
        """
        try:
            db.session.query(SeatSuggestion).delete()
            db.session.query(Booking).delete()
            db.session.query(TemperatureReading).delete()
            db.session.query(RoomEnergyState).delete()
            db.session.query(Seat).delete()
            db.session.query(Room).delete()
            db.session.query(User).filter(User.role == "student").delete()
            db.session.commit()

            return {"message": "Database cleaned"}, 200
        except Exception as e:
            db.session.rollback()
            logger.exception("Failed to clear database")
            return {"error": "Failed to clear database", "details": str(e)}, 500


# POPULATE ROOMS & SEATS

@demo_bp.route("/demo/populate-rooms-seats")
class DemoPopulateRoomsSeats(MethodView):
    def post(self):
        """
        Crea 3 stanze:
        - cold_room (north)
        - medium_room (east)
        - hot_room (south)
        con 10 posti ciascuna
        """
        try:
            rooms_data = [
                ("Cold Room", "north"),
                ("Medium Room", "east"),
                ("Hot Room", "south"),
            ]

            for name, exposure in rooms_data:
                room = Room(name=name, sun_exposure=exposure)
                db.session.add(room)
                db.session.flush()

                for i in range(10):
                    seat = Seat(
                        room_id=room.id,
                        label=f"{name[:1]}-{i+1}",
                        is_active=True
                    )
                    db.session.add(seat)

            db.session.commit()
            return {"message": "Rooms and seats created"}, 201
        except Exception as e:
            db.session.rollback()
            logger.exception("Failed to populate rooms and seats")
            return {"error": "Failed to populate rooms and seats", "details": str(e)}, 500

# POPULATE USERS

@demo_bp.route("/demo/populate-users")
class DemoPopulateUsers(MethodView):
    def post(self):
        """
        Crea utenti fittizi per demo.
        """
        try:
            count = request.json.get("count", 5)

            for i in range(count):
                user = User(
                    username=f"student{i+1}",
                    password="demo",
                    first_name="Demo",
                    last_name=f"User{i+1}",
                    email=f"student{i+1}@demo.local",
                    role="student"
                )
                db.session.add(user)

            db.session.commit()
            return {"created": count}, 201
        except Exception as e:
            db.session.rollback()
            logger.exception("Failed to populate users")
            return {"error": "Failed to populate users", "details": str(e)}, 500
# POPULATE TEMPERATURES
@demo_bp.route("/demo/populate-temperatures")
class DemoPopulateTemperatures(MethodView):
    def post(self):
        """
        Genera temperature coerenti con il tipo di stanza.
        """
        try:
            rooms = Room.query.all()
            now = datetime.utcnow()

            for room in rooms:
                if room.sun_exposure == "north":
                    base = 20
                elif room.sun_exposure == "east":
                    base = 22
                else:
                    base = 25

                for d in range(30):
                    t = TemperatureReading(
                        room_id=room.id,
                        temperature=base + random.uniform(-1, 1),
                        timestamp=now - timedelta(days=d)
                    )
                    db.session.add(t)

            db.session.commit()
            return {"message": "Temperature history populated"}, 201
        except Exception as e:
            db.session.rollback()
            logger.exception("Failed to populate temperatures")
            return {"error": "Failed to populate temperatures", "details": str(e)}, 500

# POPULATE BOOKINGS

@demo_bp.route("/demo/populate-bookings")
class DemoPopulateBookings(MethodView):
    def post(self):
        """
        Crea prenotazioni storiche per calcolo occupancy.
        """
        try:
            users = User.query.filter_by(role="student").all()
            seats = Seat.query.all()
            now = datetime.utcnow()

            created = 0
            for user in users:
                for _ in range(random.randint(10, 25)):
                    seat = random.choice(seats)
                    start = now - timedelta(days=random.randint(1, 180))
                    booking = Booking(
                        user_id=user.id,
                        seat_id=seat.id,
                        start_time=start,
                        end_time=start + timedelta(hours=2),
                        status=BookingStatus.CONFIRMED
                    )
                    db.session.add(booking)
                    created += 1

            db.session.commit()
            return {"created": created}, 201
        except Exception as e:
            db.session.rollback()
            logger.exception("Failed to populate bookings")
            return {"error": "Failed to populate bookings", "details": str(e)}, 500

# SET ROOM ENERGY STATE
@demo_bp.route("/demo/set-room-energy")
class DemoSetRoomEnergy(MethodView):
    def post(self):
        """
        Imposta stato energetico stanza (luci / AC).
        """
        try:
            data = request.json
            room_id = data["room_id"]

            state = RoomEnergyState.query.filter_by(room_id=room_id).first()
            if not state:
                state = RoomEnergyState(room_id=room_id)

            state.lights_on = data.get("lights_on", False)
            state.ac_on = data.get("ac_on", False)
            state.target_temperature = data.get("target_temperature")

            db.session.add(state)
            db.session.commit()

            return {"message": "Energy state updated"}, 200
        except Exception as e:
            db.session.rollback()
            logger.exception("Failed to set room energy state")
            return {"error": "Failed to set room energy state", "details": str(e)}, 500
# RUN FULL SCENARIO
@demo_bp.route("/demo/run-scenario")
class DemoRunScenario(MethodView):
    def post(self):
        """
        Esegue tutta la demo in un colpo solo.
        """
        try:
            DemoClearAll().post()
            DemoPopulateRoomsSeats().post()
            DemoPopulateUsers().post()
            DemoPopulateTemperatures().post()
            DemoPopulateBookings().post()

            return {"message": "Demo scenario ready"}, 200
        except:
            logger.exception("Failed to run scenario")
            raise