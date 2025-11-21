import logging

# Configurazione del logger
logging.basicConfig(
    level=logging.INFO,  # Livello di logging (INFO, DEBUG, ERROR, ecc.)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  
    handlers=[
        logging.StreamHandler()  # Invia i log alla console
    ]
)

# Crea un'istanza del logger
logger = logging.getLogger("library-booking-system")