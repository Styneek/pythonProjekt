import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(log_file='app.log', level=logging.INFO):
    logger = logging.getLogger('hotel_reservation_app')
    logger.setLevel(level)

    if not logger.handlers:
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(os.path.join(log_dir, log_file), 
                                            maxBytes=1024*1024, backupCount=5,
                                            encoding='utf-8')
        file_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

