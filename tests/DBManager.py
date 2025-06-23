###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###


import subprocess

from tests import Config

import sqlalchemy


ALEMBIC_CONFIG_FILE = 'tests/resources/alembic_test.ini'


class DBManager:

    connection = None

    def __init__(self):
        pass

    def connect(self):
        config = Config.read_config()
        engine = sqlalchemy.create_engine(config['meteo.database']['url'])
        self.connection = engine.connect()
        return self.connection

    def disconnect(self):
        self.connection.close()

    @staticmethod
    def init_complete_database():
        subprocess.run(['alembic', '-c', ALEMBIC_CONFIG_FILE, 'upgrade', 'head'], check=False)

    @staticmethod
    def remove_complete_database():
        subprocess.run(['alembic', '-c', ALEMBIC_CONFIG_FILE, 'downgrade', 'base'], check=False)
