from functools import wraps
from flask import g
from src.backend.auth.auth import auth_required
from src.backend.models.user import User
from src.backend.common.logger import logger

def admin_required(func):
    """
    Permette accesso solo agli utenti con ruolo 'admin'
    """
    @wraps(func)
    @auth_required
    def wrapper(*args, **kwargs):
        user = User.query.filter_by(username=g.user).first()
        if not user or user.role != "admin":
            logger.warning(f"Accesso admin negato per utente {g.user}")
            return {"error": "Admin privileges required"}, 403
        return func(*args, **kwargs)
    return wrapper
