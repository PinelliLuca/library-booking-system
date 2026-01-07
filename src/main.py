from flask import Flask
from flask_smorest import Api
from src.backend.common.extensions import db, jwt, mail
from dotenv import load_dotenv
from datetime import timedelta
import os
from flask import jsonify, send_from_directory
from werkzeug.exceptions import HTTPException
from src.backend.controllers.user_controller import user_bp
from src.backend.controllers.booking_controller import booking_bp
from src.backend.controllers.seat_controller import seats_bp
from src.backend.controllers.login import login_bp
from src.backend.controllers.seat_occupancy import occupancy_bp
from src.backend.controllers.room_controller import room_bp
from src.backend.controllers.energy_command import energy_bp
from src.backend.controllers.seat_suggestion import suggestion_bp
from src.backend.controllers.temperature_readings import temperature_bp

# Carica variabili da .env
load_dotenv()

# Inizializza Flask
app = Flask(__name__, instance_relative_config=True)
app.config["API_TITLE"] = "IoT Parking API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # Cambia con una chiave sicura
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=120)

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'false').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@example.com')


app.register_blueprint(login_bp)
app.register_blueprint(user_bp)
app.register_blueprint(seats_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(occupancy_bp)
app.register_blueprint(room_bp)
app.register_blueprint(energy_bp)
app.register_blueprint(suggestion_bp)
app.register_blueprint(temperature_bp, url_prefix="/api")
# Configurazione SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance')), 'iot.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

print("DB PATH:", app.config["SQLALCHEMY_DATABASE_URI"])
print("ABSOLUTE PATH:", os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'iot.db')))


# Inizializza estensioni
db.init_app(app)
api = Api(app)
jwt.init_app(app)
mail.init_app(app)
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

@app.route("/frontend/mappa")
def serve_frontend_mappa():
    return send_from_directory("frontend", "index.html")

@app.route("/frontend/login")
def serve_frontend_login():
    return send_from_directory("frontend", "login.html")

@app.route("/frontend/register")
def serve_frontend_register():
    return send_from_directory("frontend", "register.html")
# Crea le tabelle se non esistono
with app.app_context():
    db.create_all()

# Endpoint di test
@app.route("/")
def home():
    return {"message": "IoT Parking API attiva"}

if __name__ == "__main__":
    app.run(debug=True)
