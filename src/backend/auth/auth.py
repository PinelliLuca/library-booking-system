from flask_jwt_extended import jwt_required,get_jwt_identity
from flask import g

def auth_required(func):
    """
    Decoratore per proteggere le route che richiedono autenticazione.
    """
    @jwt_required()
    def wrapper(*args, **kwargs):
        g.user = get_jwt_identity()  # Ottieni l'identità dell'utente dal token
        return func(*args, **kwargs)
    return wrapper