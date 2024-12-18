import logging
import os

def init_logger_no_rotation():
    """
    Initialize logger without RotatingFileHandler
    :return:
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Ensure log directory exists
    if not os.path.exists("log"):
        os.makedirs("log")

    # Formatter for log messages
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s : [%(levelname)s] %(message)s"
    )

    # Stream handler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File handler for general logging
    file_handler = logging.FileHandler("log/pricetracker.log")
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
