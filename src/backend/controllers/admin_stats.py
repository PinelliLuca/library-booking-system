from datetime import datetime, timedelta
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.backend.common.extensions import db
from src.backend.models import Room, Seat, TemperatureReading, RoomEnergyState, EnergyCommand, Booking, User
from sqlalchemy.exc import SQLAlchemyError
from flask import request

admin_bp = Blueprint("admin", __name__, description="Admin statistics")


def _require_admin(username):
    user = User.query.filter_by(username=username).first()
    return user and user.role == 'admin'


@admin_bp.route('/admin/stats/overview', methods=['GET'])
@jwt_required()
def admin_stats_overview():
    try:
        username = get_jwt_identity()
        if not _require_admin(username):
            return {"error": "Forbidden"}, 403

        now = datetime.now()
        start = request.args.get('start')
        end = request.args.get('end')

        if end:
            try:
                end_ts = datetime.fromisoformat(end)
            except Exception:
                end_ts = now
        else:
            end_ts = now

        if start:
            try:
                start_ts = datetime.fromisoformat(start)
            except Exception:
                start_ts = end_ts - timedelta(hours=24)
        else:
            start_ts = end_ts - timedelta(hours=24)

        rooms = Room.query.all()

        total_seats = 0
        total_occupied = 0
        temp_acc = 0.0
        temp_count = 0

        rooms_out = []
        for room in rooms:
            seats = room.seats or []
            total = len(seats)
            occupied = sum(1 for s in seats if s.is_occupied)

            # average temperature for this room in the time window
            temps = (
                TemperatureReading.query
                .filter(TemperatureReading.room_id == room.id)
                .filter(TemperatureReading.timestamp >= start_ts)
                .filter(TemperatureReading.timestamp <= end_ts)
                .all()
            )
            if temps:
                avg_temp = sum(t.temperature for t in temps) / len(temps)
            else:
                avg_temp = None

            energy = RoomEnergyState.query.filter_by(room_id=room.id).first()
            lights_on = bool(energy and energy.lights_on)

            rooms_out.append({
                "id": room.id,
                "name": room.name,
                "total_seats": total,
                "occupied_now": occupied,
                "occupancy_rate": (occupied / total * 100) if total else 0,
                "avg_temp": avg_temp,
                "lights_on": lights_on,
            })

            total_seats += total
            total_occupied += occupied
            if avg_temp is not None:
                temp_acc += avg_temp
                temp_count += 1

        global_avg_temp = (temp_acc / temp_count) if temp_count else None

        payload = {
            "timestamp": end_ts.isoformat(),
            "rooms": rooms_out,
            "global": {
                "total_rooms": len(rooms),
                "total_seats": total_seats,
                "occupied_now": total_occupied,
                "occupancy_rate": (total_occupied / total_seats * 100) if total_seats else 0,
                "avg_temp": global_avg_temp,
            },
        }

        return payload, 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return {"error": "Database error", "details": str(e)}, 500
    except Exception as e:
        return {"error": "Internal error", "details": str(e)}, 500


@admin_bp.route('/admin/stats/occupancy', methods=['GET'])
@jwt_required()
def admin_stats_occupancy():
    """Return time-series occupancy counts aggregated by resolution (hour/day)."""
    try:
        username = get_jwt_identity()
        if not _require_admin(username):
            return {"error": "Forbidden"}, 403

        room_id = request.args.get('room_id', type=int)
        start = request.args.get('start')
        end = request.args.get('end')
        resolution = request.args.get('resolution', 'hour')

        now = datetime.now()
        if end:
            try:
                end_ts = datetime.fromisoformat(end)
            except Exception:
                end_ts = now
        else:
            end_ts = now

        if start:
            try:
                start_ts = datetime.fromisoformat(start)
            except Exception:
                start_ts = end_ts - timedelta(days=7)
        else:
            start_ts = end_ts - timedelta(days=7)

        # build time buckets
        delta = timedelta(hours=1) if resolution == 'hour' else timedelta(days=1)
        buckets = []
        cur = start_ts
        while cur < end_ts:
            buckets.append((cur, min(cur + delta, end_ts)))
            cur += delta

        series = []
        for s, e in buckets:
            # count seats with confirmed booking overlapping this bucket
            q = Booking.query.filter(Booking.status == 'confirmed')
            if room_id:
                q = q.join(Seat).filter(Seat.room_id == room_id)
            q = q.filter(Booking.start_time < e).filter(Booking.end_time > s)
            count = q.with_entities(db.func.count(db.func.distinct(Booking.seat_id))).scalar() or 0
            series.append({"start": s.isoformat(), "end": e.isoformat(), "occupied_seats": int(count)})

        return {"series": series}, 200
    except Exception as e:
        return {"error": "Internal error", "details": str(e)}, 500


@admin_bp.route('/admin/stats/bookings', methods=['GET'])
@jwt_required()
def admin_stats_bookings():
    """Return booking counts and top/bottom seats in the period."""
    try:
        username = get_jwt_identity()
        if not _require_admin(username):
            return {"error": "Forbidden"}, 403

        room_id = request.args.get('room_id', type=int)
        start = request.args.get('start')
        end = request.args.get('end')

        now = datetime.now()
        if end:
            try:
                end_ts = datetime.fromisoformat(end)
            except Exception:
                end_ts = now
        else:
            end_ts = now

        if start:
            try:
                start_ts = datetime.fromisoformat(start)
            except Exception:
                start_ts = end_ts - timedelta(days=30)
        else:
            start_ts = end_ts - timedelta(days=30)

        q = Booking.query.filter(Booking.start_time >= start_ts).filter(Booking.start_time <= end_ts)
        if room_id:
            q = q.join(Seat).filter(Seat.room_id == room_id)

        total_bookings = q.count()

        # top seats by bookings
        top = (
            q.with_entities(Booking.seat_id, db.func.count(Booking.id).label('cnt'))
            .group_by(Booking.seat_id)
            .order_by(db.desc('cnt'))
            .limit(10)
            .all()
        )
        top_list = [{'seat_id': t.seat_id, 'count': t.cnt} for t in top]

        return {"total_bookings": total_bookings, "top_seats": top_list}, 200

    except Exception as e:
        return {"error": "Internal error", "details": str(e)}, 500


@admin_bp.route('/admin/stats/temperatures', methods=['GET'])
@jwt_required()
def admin_stats_temperatures():
    """Return temperature time-series (avg) per resolution"""
    try:
        username = get_jwt_identity()
        if not _require_admin(username):
            return {"error": "Forbidden"}, 403

        room_id = request.args.get('room_id', type=int)
        start = request.args.get('start')
        end = request.args.get('end')
        resolution = request.args.get('resolution', 'hour')

        now = datetime.now()
        if end:
            try:
                end_ts = datetime.fromisoformat(end)
            except Exception:
                end_ts = now
        else:
            end_ts = now

        if start:
            try:
                start_ts = datetime.fromisoformat(start)
            except Exception:
                start_ts = end_ts - timedelta(days=7)
        else:
            start_ts = end_ts - timedelta(days=7)

        delta = timedelta(hours=1) if resolution == 'hour' else timedelta(days=1)
        buckets = []
        cur = start_ts
        while cur < end_ts:
            buckets.append((cur, min(cur + delta, end_ts)))
            cur += delta

        series = []
        for s, e in buckets:
            q = TemperatureReading.query.filter(TemperatureReading.timestamp >= s).filter(TemperatureReading.timestamp < e)
            if room_id:
                q = q.filter(TemperatureReading.room_id == room_id)
            temps = q.with_entities(db.func.avg(TemperatureReading.temperature)).scalar()
            series.append({"start": s.isoformat(), "end": e.isoformat(), "avg_temp": float(temps) if temps is not None else None})

        return {"series": series}, 200
    except Exception as e:
        return {"error": "Internal error", "details": str(e)}, 500


@admin_bp.route('/admin/stats/energy', methods=['GET'])
@jwt_required()
def admin_stats_energy():
    """Return energy events (lights on/off) counts and current states."""
    try:
        username = get_jwt_identity()
        if not _require_admin(username):
            return {"error": "Forbidden"}, 403

        room_id = request.args.get('room_id', type=int)
        start = request.args.get('start')
        end = request.args.get('end')

        now = datetime.now()
        if end:
            try:
                end_ts = datetime.fromisoformat(end)
            except Exception:
                end_ts = now
        else:
            end_ts = now

        if start:
            try:
                start_ts = datetime.fromisoformat(start)
            except Exception:
                start_ts = end_ts - timedelta(days=30)
        else:
            start_ts = end_ts - timedelta(days=30)

        q = EnergyCommand.query.filter(EnergyCommand.timestamp >= start_ts).filter(EnergyCommand.timestamp <= end_ts)
        if room_id:
            q = q.filter(EnergyCommand.room_id == room_id)

        total_commands = q.count()
        lights_commands = q.filter(EnergyCommand.command_type.in_(['lights_on','lights_off'])).count()

        # current states
        states_q = RoomEnergyState.query
        if room_id:
            states_q = states_q.filter_by(room_id=room_id)
        states = [{"room_id": s.room_id, "lights_on": bool(s.lights_on), "ac_on": bool(s.ac_on), "target_temperature": s.target_temperature} for s in states_q.all()]

        return {"total_commands": total_commands, "lights_commands": lights_commands, "states": states}, 200

    except Exception as e:
        return {"error": "Internal error", "details": str(e)}, 500
