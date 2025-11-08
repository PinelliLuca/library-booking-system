from flask import Flask, send_from_directory
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from extensions import db
import models

# from werkzeug.utils import send_from_directory

# Carica variabili da .env
load_dotenv()

# Inizializza Flask
app = Flask(__name__)
app.config["API_TITLE"] = "IoT Parking API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"

# Configurazione SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../instance/iot.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inizializza estensioni
db.init_app(app)
api = Api(app)

# Crea le tabelle se non esistono
with app.app_context():
    db.create_all()

from seats import seats_bp
app.register_blueprint(seats_bp)
@app.route("/frontend")
def serve_frontend():
    return send_from_directory("frontend", "index.html")

# Endpoint di test
@app.route("/")
def home():
    return {"message": "IoT Parking API attiva"}

if __name__ == "__main__":
    app.run(debug=True)
