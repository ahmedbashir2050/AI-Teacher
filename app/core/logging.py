import logging
from pythonjsonlogger import jsonlogger
import sys

def configure_logging():
    """
    Configures a structured JSON logger.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Use a handler that supports JSON formatting
    logHandler = logging.StreamHandler(sys.stdout)

    # Define the format of the JSON logs
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(module)s %(funcName)s %(lineno)d'
    )

    logHandler.setFormatter(formatter)

    # Avoid adding duplicate handlers
    if not logger.handlers:
        logger.addHandler(logHandler)

# Configure logging on import
configure_logging()

def get_logger(name: str):
    """
    Returns a logger instance.
    """
    return logging.getLogger(name)
