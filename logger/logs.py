###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###
import logging
import logging.handlers
import threading
import sys

_logger_lock = threading.Lock()

def setup_custom_logger(name, log_level):
    with _logger_lock:
        logger = logging.getLogger(name)
        if not getattr(logger, '_custom_handler_set', False):
            formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
            handler = logging.handlers.RotatingFileHandler(name + '.log', encoding='utf-8', maxBytes=10**6, backupCount=5)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            # logger.addHandler(logging.StreamHandler(sys.stdout))
            logger._custom_handler_set = True
        logger.setLevel(logging.getLevelName(log_level))
        return logger

