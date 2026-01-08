from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from src.backend.models.user import User
from src.backend.auth.token_generator import generate_token

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['POST'])
def login():
    """
    Effettua il login di un utente e restituisce un token JWT.
    """
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        # Verifica credenziali
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            token = generate_token(identity=user.username)
            return jsonify({"access_token": token, "role": user.role}), 200

        return jsonify({"message": "Credenziali non valide"}), 401
    except Exception as e:
        return jsonify({"message": "Errore durante il login", "error": str(e)}), 500

@login_bp.route('/logout', methods=['POST'])
def logout():
    """
    Effettua il logout (opzionale, lato client si può semplicemente eliminare il token).
    """
    return jsonify({"message": "Logout effettuato con successo"}), 200