from flask import Blueprint, jsonify, request
from src.main import db
from src.backend.seat.models import Seat

seats_bp = Blueprint("seats", __name__, url_prefix="/seats")

@seats_bp.route("/", methods=["GET"])
def get_all_seats():
    seats = Seat.query.all()
    return jsonify([
        {
            "row": seat.row,
            "column": seat.column,
            "is_occupied": seat.is_occupied
        } for seat in seats
    ])

@seats_bp.route("/<int:row>/<int:column>", methods=["GET"])
def get_single_seat(row, column):
    seat = Seat.query.get((row, column))
    if not seat:
        return jsonify({"error": "Seat not found"}), 404
    return jsonify({
        "row": seat.row,
        "column": seat.column,
        "is_occupied": seat.is_occupied
    })
# PATCH: modifica lo stato di occupazione
@seats_bp.route("/<int:seat_id>", methods=["PATCH"])
def update_seat_status(seat_id):
    seat = Seat.query.get(seat_id)
    if not seat:
        return jsonify({"error": "Seat not found"}), 404

    data = request.get_json()
    if "is_occupied" not in data:
        return jsonify({"error": "Missing 'is_occupied' field"}), 400

    seat.is_occupied = data["is_occupied"]
    db.session.commit()
    return jsonify({
        "id": seat.id,
        "is_occupied": seat.is_occupied
    })
"""
es di chiamata che verrà eseguita dall'arduino
fetch("http://localhost:5000/seats/12", {
  method: "PATCH",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ is_occupied: true })
});
"""