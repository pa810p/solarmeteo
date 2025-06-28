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
    logging.basicConfig(
        level=logging.getLevelName(log_level),  # Default level (override per-module later)
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(name + '.log', encoding='utf-8', maxBytes=10**6, backupCount=5),
            logging.StreamHandler(sys.stdout)  # Optional: also print to console
        ]
    )


