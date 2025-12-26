from src.backend.common.extensions import db

class UserToken(db.Model):
    __tablename__ = "user_token"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    token = db.Column(db.String(36), nullable=False, unique=True)
    issued_at = db.Column(db.DateTime, nullable=False)
    expired_at = db.Column(db.DateTime, nullable=False)

    #user = db.relationship('User', backref=db.backref('user_token', uselist=False))
    user = db.relationship("User", back_populates="tokens")