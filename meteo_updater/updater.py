###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###


import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Updater:

    def __init__(self, meteo_db_url, updater_interval, logger):
        self.meteo_db_url = meteo_db_url
        self.updater_interval = updater_interval
        self.logger = logger

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
        self.logger.debug('GET: %s status code: %s' % (url, str(response.status_code)))
        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error('Error downloading solar information.')
            raise Exception('Error downloading solar information.')

