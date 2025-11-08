from flask import Flask
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from werkzeug.utils import send_from_directory
from flask_jwt_extended import JWTManager
from datetime import timedelta
from src.backend.auth.login import login_bp
from src.backend.auth.user import user_bp
from flask_mail import Mail
import os
from src.backend.seat.service import seats_bp
from flask import jsonify
from flask import jsonify
from werkzeug.exceptions import HTTPException

# Carica variabili da .env
load_dotenv()

# Inizializza Flask
app = Flask(__name__)
app.config["API_TITLE"] = "IoT Parking API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # Cambia con una chiave sicura
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=120)


mail=Mail(app)

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'false').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@example.com')

jwt = JWTManager(app)
app.register_blueprint(login_bp)
app.register_blueprint(user_bp)
# Configurazione SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../instance/iot.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inizializza estensioni
db = SQLAlchemy(app)
api = Api(app)

# Gestione delle eccezioni HTTP
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """
    Gestisce le eccezioni HTTP restituendo un messaggio di errore standard.
    """
    return jsonify({"error": e.name, "message": e.description}), e.code

# Gestione delle eccezioni generiche
@app.errorhandler(Exception)
def handle_generic_exception(e):
    """
    Gestisce le eccezioni generiche restituendo un messaggio di errore standard.
    """
    return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

# Gestione degli errori JWT
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """
    Gestisce il caso in cui il token JWT è scaduto.
    """
    return jsonify({"message": "Token scaduto", "error": "token_expired"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    """
    Gestisce il caso in cui il token JWT è invalido.
    """
    return jsonify({"message": "Token non valido", "error": "invalid_token"}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    """
    Gestisce il caso in cui il token JWT è mancante.
    """
    return jsonify({"message": "Token mancante", "error": "authorization_required"}), 401


app.register_blueprint(seats_bp)
@app.route("/frontend")
def serve_frontend():
    return send_from_directory("../frontend", "index.html")
# Crea le tabelle se non esistono
with app.app_context():
    db.create_all()

# Endpoint di test
@app.route("/")
def home():
    return {"message": "IoT Parking API attiva"}

if __name__ == "__main__":
    app.run(debug=True)
