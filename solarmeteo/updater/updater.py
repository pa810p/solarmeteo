###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###


import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from logging import getLogger

logger = getLogger(__name__)

class Updater:

    def __init__(self, meteo_db_url, updater_interval):
        """
        Base class of updaters

        :param meteo_db_url:
        :param updater_interval: obsolete, daemon mode will not be used anymore
        """
        self.meteo_db_url = meteo_db_url
        self.updater_interval = updater_interval

    def create_connection(self):
        """
        Creates connection to database
        """
        engine = create_engine(self.meteo_db_url)
        return engine.connect()

    def create_session(self):
        """
        Creates a database session
        """
        session = sessionmaker(bind=self.create_connection())
        return session()

    def get(self, url):
        response = requests.get(url)
        logger.debug('GET: %s status code: %s' % (url, str(response.status_code)))
        if response.status_code == 200:
            return response.json()
        else:
            logger.error('Error downloading solar information.')
            raise Exception('Error downloading solar information.')

