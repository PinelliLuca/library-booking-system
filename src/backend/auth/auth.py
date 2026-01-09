from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import g

def auth_required(func):
    """
    Decoratore per proteggere le route che richiedono autenticazione JWT.
    Imposta g.user con lo username autenticato.
    """
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        g.user = get_jwt_identity()
        return func(*args, **kwargs)
    return wrapper
