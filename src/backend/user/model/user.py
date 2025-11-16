from src.backend.common.extensions import db
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String,unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    token = db.Column(db.String, nullable=False)
    mail = db.Column(db.Boolean, default=False)
   # upd_user=db.Column(db.String)
   # ins_user=db.Column(db.String)
    ins_istance=db.Column(db.DateTime, default=db.func.current_timestamp())