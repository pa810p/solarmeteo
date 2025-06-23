###
# SolarMeteo    : https://github.com/pa810p/rpg
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###


import configparser
import os.path

import alembic
import sqlalchemy
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class SolarMeteoTestConfig:

    SOLARMETEO_ROOT=os.getenv('SOLARMETEO_ROOT')

    ALEMBIC_CONFIG_FILE = SOLARMETEO_ROOT + '/tests/resources/alembic_test.ini'
    ALEMBIC_LOCATION = SOLARMETEO_ROOT + '/alembic'
    METEO_PROPERTIES = SOLARMETEO_ROOT + '/tests/resources/meteo_test.properties'

    connection = None
    session = None

    def __init__(self):
        if os.path.exists(self.ALEMBIC_CONFIG_FILE):
            self.config = Config(self.ALEMBIC_CONFIG_FILE)

        if os.path.exists(self.ALEMBIC_LOCATION):
            self.config.set_main_option('script_location', self.ALEMBIC_LOCATION)

        if os.path.exists(self.METEO_PROPERTIES):
            self.meteoconfig = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
            self.meteoconfig.read(self.METEO_PROPERTIES)


    def create_connection(self, db_url):
        engine = create_engine(db_url)
        return engine.connect()


    def create_session(self):
        """
        Creates a database session
        """
        session = sessionmaker(bind = self.create_connection(self.meteoconfig['meteo.database']['url']))
        return session()

    def connect(self):
        engine = sqlalchemy.create_engine(self.meteoconfig['meteo.database']['url'])
        self.connection = engine.connect()
        return self.connection

    def disconnect(self):
        self.connection.close()

    def init_complete_database(self):
        self.remove_complete_database()
        alembic.command.upgrade(self.config, revision='head')

    def remove_complete_database(self):
        try:
            alembic.command.downgrade(self.config, revision='base')
        except Exception as e:
            print("FATAL: %s" %e)

    def __getitem__(self, key):
        return self.meteoconfig[key]
