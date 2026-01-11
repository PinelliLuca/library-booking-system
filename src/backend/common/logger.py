import logging
import sys

logger = logging.getLogger("library-booking-system")
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)

logger.handlers.clear()
logger.addHandler(handler)
logger.propagate = False
