###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

import logging.handlers
import sys


def setup_custom_logger(name, log_level):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    handler = logging.handlers.RotatingFileHandler(name + '.log', encoding='utf-8')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.getLevelName(log_level))
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    return logger

