from flask import g, current_app
from flask_mail import Message
from src.main import mail
from src.backend.user.model.user import User

def send_email(subject, body, recipients=None):
    """
    Invia un'email all'utente autenticato o a destinatari specificati.
    :param subject: Oggetto dell'email
    :param body: Corpo dell'email
    :param recipients: Lista di destinatari (opzionale, altrimenti usa l'email dell'utente autenticato)
    """
    # Recupera l'utente autenticato
    if not recipients:
        if not hasattr(g, 'user'):
            raise ValueError("Utente non autenticato")
        
        user = User.query.filter_by(username=g.user).first()
        if not user or not user.mail:
            raise ValueError("Email non trovata per l'utente autenticato")
        
        recipients = [user.mail]

    # Crea il messaggio
    msg = Message(
        subject=subject,
        recipients=recipients,
        body=body,
        sender=current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@example.com")
    )

    # Invia l'email
    mail.send(msg)