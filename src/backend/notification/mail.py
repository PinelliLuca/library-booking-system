from flask import current_app
from flask_mail import Message
from src.backend.common.extensions import mail
from src.backend.models.user import User
from src.backend.common.logger import logging


def send_email(subject, body, recipients):
    """
    Invia un'email ai destinatari specificati.
    :param subject: Oggetto dell'email
    :param body: Corpo dell'email
    :param recipients: Lista di email (obbligatoria)
    """
    if not recipients:
        raise ValueError("Nessun destinatario specificato per l'email")

    msg = Message(
        subject=subject,
        recipients=recipients,
        body=body,
        sender=current_app.config.get("MAIL_DEFAULT_SENDER")
    )

    try:
        mail.send(msg)
        logging.info(f"Email inviata a {recipients} con oggetto '{subject}'")
    except Exception as e:
        logging.error(f"Errore durante l'invio dell'email: {str(e)}")
        raise
