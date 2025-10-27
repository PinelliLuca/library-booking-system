from flask import Blueprint, jsonify
from models import Seat
from main import db

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
