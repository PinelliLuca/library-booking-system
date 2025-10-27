from flask import Flask
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

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
db = SQLAlchemy(app)
api = Api(app)

from seats import seats_bp
app.register_blueprint(seats_bp)

# Crea le tabelle se non esistono
with app.app_context():
    db.create_all()

# Endpoint di test
@app.route("/")
def home():
    return {"message": "IoT Parking API attiva"}

if __name__ == "__main__":
    app.run(debug=True)
