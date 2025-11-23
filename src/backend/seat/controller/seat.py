from flask import Blueprint, jsonify, request
from src.backend.common.extensions import db
from src.backend.seat.models import Seat
from src.backend.notification.mail import send_email
from src.backend.auth.auth import auth_required
from sqlalchemy.exc import SQLAlchemyError

seats_bp = Blueprint("seats", __name__, url_prefix="/seats")

@seats_bp.route("/", methods=["GET"])
def get_all_seats():
    try:
        seats = Seat.query.all()
        return jsonify([
            {
                "id": seat.id,
                "is_occupied": seat.is_occupied
            } for seat in seats
        ])
    except SQLAlchemyError as e:
        return jsonify({"error": "Errore del database", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Errore interno del server", "details": str(e)}), 500

@seats_bp.route("/<int:row>/<int:column>", methods=["GET"])
def get_single_seat(row, column):
    try:
        seat = Seat.query.get((row, column))
        if not seat:
            return jsonify({"error": "Seat not found"}), 404
        return jsonify({
            "id": seat.id,
            "is_occupied": seat.is_occupied
        })
    except SQLAlchemyError as e:
        return jsonify({"error": "Errore del database", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Errore interno del server", "details": str(e)}), 500

# PATCH: modifica lo stato di occupazione
@seats_bp.route("/<int:seat_id>", methods=["PATCH"])
@auth_required
def update_seat_status(seat_id):
    try:
        seat = Seat.query.get(seat_id)
        if not seat:
            return jsonify({"error": "Seat not found"}), 404

        data = request.get_json()
        if "is_occupied" not in data:
            return jsonify({"error": "Missing 'is_occupied' field"}), 400
        booking = data.get('booking')
        if not seat_id:
            return jsonify({"error": "Missing 'seat_id'"}), 400
        if not booking:
            return jsonify({"error": "specifica il booking"}), 500
        seat = Seat.query.get(seat_id)
        if not seat:
            return jsonify({"error": "Seat not found"}), 404
        if seat.is_occupied and booking == True:
            return jsonify({"error": "Seat already booked"}), 400
        elif booking == False and seat.is_occupied == False:
            return jsonify({"error": "Seat already free"}), 400
        elif booking == False and seat.is_occupied == True:
            seat.is_occupied = False
            db.session.commit()
        else:
            seat.is_occupied = True
            db.session.commit()

        try:
            send_email(
                subject="Conferma prenotazione",
                body=f"Hai prenotato il posto {seat_id}.",
            )
            return jsonify({
                "id": seat.id,
                "is_occupied": seat.is_occupied
            })
        except Exception as e:
            return jsonify({"error": "Errore durante l'invio dell'email", "details": str(e)}), 500

    except SQLAlchemyError as e:
        db.session.rollback()  # Annulla eventuali modifiche non salvate
        return jsonify({"error": "Errore del database", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Errore interno del server", "details": str(e)}), 500
"""
es di chiamata che verrà eseguita dall'arduino
fetch("http://localhost:5000/seats/12", {
  method: "PATCH",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ is_occupied: true })
});
"""
