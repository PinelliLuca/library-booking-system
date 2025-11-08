from flask_jwt_extended import jwt_required

def auth_required(func):
    """
    Decoratore per proteggere le route che richiedono autenticazione.
    """
    @jwt_required()
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper