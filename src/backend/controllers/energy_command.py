from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required
from src.backend.common.extensions import db
from src.backend.models import EnergyCommand

energy_bp = Blueprint("energy", __name__)

@energy_bp.route("/energy-command")
class EnergyCommandAPI(MethodView):

    @jwt_required()
    def post(self):
        data = request.get_json()

        try:
            cmd = EnergyCommand(
                room_id=data["room_id"],
                command_type=data["command_type"],
                value=data.get("value"),
                issued_by="admin"
            )
            db.session.add(cmd)
            db.session.commit()
            return {"message": "Command issued"}, 201

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
