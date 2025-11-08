from src.main import db
class UserToken(db.Model):
    __tablename__ = "user_token"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_id'), nullable=False)
    token = db.Column(db.String, nullable=False)
    issued_at = db.Column(db.DateTime, nullable=False)
    expired_at = db.Column(db.DateTime, nullable=False)
    user=db.relationship('User', backref=db.backref('user_token', uselist=False))
