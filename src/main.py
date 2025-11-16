from flask import Flask, send_from_directory
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
# from werkzeug.utils import send_from_directory
from flask_jwt_extended import JWTManager
from datetime import timedelta
from src.backend.auth.login import login_bp
# from src.backend.auth.user import user_bp
from flask_mail import Mail
import os
from src.backend.seat.service import seats_bp
from flask import jsonify
from src.extensions import db


# Carica variabili da .env
load_dotenv()

# calcola project root (uno sopra src) e istanzia instance_dir lì
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
instance_dir = os.path.join(project_root, "instance")
os.makedirs(instance_dir, exist_ok=True)

# crea l'app usando instance_path esplicito
app = Flask(__name__, instance_path=instance_dir, instance_relative_config=True)

# usa il percorso assoluto dentro instance_dir per il DB
db_path = os.path.join(instance_dir, "iot.db")

app.config["API_TITLE"] = "IoT Parking API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # Cambia con una chiave sicura
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=120)

mail=Mail(app)

jwt = JWTManager(app)
app.register_blueprint(login_bp)
# app.register_blueprint(user_bp)
# Configurazione SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inizializza estensioni
# db = SQLAlchemy(app)
db.init_app(app)
api = Api(app)

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
@app.route("/frontend/mappa")
def serve_frontend():
    return send_from_directory("frontend", "index.html")

@app.route("/frontend/login")
def serve_frontend_login():
    return send_from_directory("frontend", "login.html")
with app.app_context():
    db.create_all()

# Endpoint di test
@app.route("/")
def home():
    return {"message": "IoT Parking API attiva"}

if __name__ == "__main__":
    app.run(debug=True)
