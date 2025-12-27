from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from src.backend.common.extensions import db
from src.backend.models.user import User
from src.backend.models.user_token import UserToken
from src.backend.auth.token_generator import generate_token
from src.backend.common.logger import logging
# Creazione del Blueprint
user_bp = Blueprint('user', __name__)

@user_bp.route('/register', methods=['POST'])
def register_user():
    """
    Permette l'iscrizione di un nuovo utente.
    Riceve i dati dell'utente tramite JSON, crea l'utente e genera un token di autenticazione.
    """
    try:
        data = request.json

        # Estrai i dati dal JSON
        username = data.get('username')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        mail = data.get('mail')

        # Controlla che tutti i campi siano presenti
        if not all([username, password, first_name, last_name, mail]):
            logging.error("Campi mancanti durante la registrazione dell'utente.")
            return jsonify({"error": "Tutti i campi sono obbligatori"}), 400

        # Controlla se l'utente esiste già
        if User.query.filter_by(username=username).first():
            logging.error("Username già in uso durante la registrazione dell'utente.")
            return jsonify({"error": "Username già in uso"}), 409

        if User.query.filter_by(mail=mail).first():
            logging.error("Email già in uso durante la registrazione dell'utente.")
            return jsonify({"error": "Email già in uso"}), 409

        # Crea un nuovo utente
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            mail=mail
        )
        db.session.add(new_user)
        db.session.commit()

        # Genera un token per l'utente
        token = generate_token(identity=username)
        expiration_time = datetime.utcnow() + timedelta(hours=2)

        # Crea un record nella tabella UserToken
        user_token = UserToken(
            user_id=new_user.id,
            token=token,
            issued_at=datetime.utcnow(),
            expired_at=expiration_time
        )
        db.session.add(user_token)
        db.session.commit()
        logging.info(f"Nuovo utente registrato: {username} - mail {mail}")
        return jsonify({
            "message": "Utente registrato con successo",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
                "mail": new_user.mail
            },
            "token": token
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()  # Annulla eventuali modifiche non salvate
        logging.error(f"Errore del database durante la registrazione dell'utente: {str(e)}")
        return jsonify({"error": "Errore del database", "details": str(e)}), 500

    except Exception as e:
        logging.error(f"Errore interno del server durante la registrazione dell'utente: {str(e)}")
        return jsonify({"error": "Errore interno del server", "details": str(e)}), 500