from flask_jwt_extended import create_access_token
from datetime import timedelta

def generate_token(identity):
    """
    Genera un token JWT per l'utente specificato.
    :param identity: Identificativo dell'utente (es. username o id)
    :return: Token JWT
    """
    return create_access_token(identity=identity)