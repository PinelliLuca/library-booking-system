from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import create_access_token

from src.backend.common.extensions import db
from src.backend.common.labels import BODY_USER_REGISTRATION
from src.backend.models.user import User
from src.backend.notification.mail import send_email

user_bp = Blueprint("users", __name__)
@user_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")

        if not all([username, password, first_name, last_name, email]):
            return {"error": "Missing required fields"}, 400

        if User.query.filter_by(username=username).first():
            return {"error": "Username already exists"}, 409

        if User.query.filter_by(email=email).first():
            return {"error": "Email already exists"}, 409

        user = User(
            username=username,
            password=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        db.session.add(user)
        db.session.commit()
        try:
            send_email(subject="Registrazione completata",
                #body=f"Ciao {user.first_name}, la tua registrazione è avvenuta con successo!",
                body=BODY_USER_REGISTRATION.format(first_name=user.first_name),
                recipients=[user.email])
        except Exception:
            raise
        return {
            "message": "User registered successfully",
            "user_id": user.id
        }, 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return {"error": "Database error", "details": str(e)}, 500
@user_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not all([username, password]):
            return {"error": "Missing credentials"}, 400

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            return {"error": "Invalid credentials"}, 401

        access_token = create_access_token(identity=username)

        return {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        }, 200

    except SQLAlchemyError as e:
        return {"error": "Database error", "details": str(e)}, 500
@user_bp.route('/test-email')
def test_email():
    try:
        send_email("Test invio", "Corpo di prova", ["238134@studenti.unimore.it"])
        return {"message": "Email inviata (in background)"}, 200
    except Exception as e:
        return {"error": "Invio fallito", "details": str(e)}, 500
