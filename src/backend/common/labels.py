BODY_USER_REGISTRATION="Ciao {first_name}, la tua registrazione è avvenuta con successo!\n\nBenvenuto a bordo!\n\nIl team di Gestione Prenotazioni."
BOOKING_FORCE_MOVE_BODY = (
    "La tua prenotazione è stata spostata.\n\n"
    "Posto precedente: {old_seat}\n"
    "Nuovo posto: {new_seat}\n\n"
    "Motivazione:\n{reason}\n\n"
    "Grazie per la collaborazione."
)

BOOKING_CONFIRMED_BODY = (
    "La tua prenotazione per il posto {seat_id} è stata confermata con successo."
)

SEAT_RELEASED_BODY = (
    "Il posto {seat_id} è stato liberato automaticamente per inattività.\n"
    "Se ritieni ci sia un errore, contatta l'amministrazione."
)
EMAIL_BOOKING_COMPLETED = {
    "subject": "Prenotazione completata",
    "body": (
        "La tua prenotazione per il posto {seat_id} si è conclusa correttamente.\n\n"
        "Orario di fine prenotazione: {end_time}\n\n"
        "Grazie per aver utilizzato il sistema di prenotazione della biblioteca."
    )
}
EMAIL_FORCE_RELEASE = {
    "subject": "Posto liberato automaticamente",
    "body": (
        "Il tuo posto {seat_id} è stato liberato automaticamente perché "
        "non è stata rilevata presenza.\n\n"
        "La prenotazione era valida fino alle {end_time}."
    )
}
