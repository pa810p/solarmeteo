###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

import unittest

from datetime import datetime
from mockito import when, mock, unstub, eq
from sqlalchemy.orm import sessionmaker

import json

from logs import logs
from meteo_updater.SolarUpdater import SolarUpdater
from test.DBManager import DBManager
from test import StationCommon, Config

IMGW_STATION_ID = 'id_stacji'

STATION1_FILE = 'test/data/station1.json'


class TestSolarUpdater(unittest.TestCase):

    dbManager = DBManager()

    updater = None

    @classmethod
    def setUpClass(cls):
        cls.dbManager.init_complete_database()
        cls.connection = cls.dbManager.connect()

        config = Config.read_config()

        logger = logs.setup_custom_logger('updater', config['meteo']['loglevel'])

        cls.updater = SolarUpdater(
            meteo_db_url=config['meteo.database']['url'],
            data_url=config['solar']['url'],
            updater_interval=config['meteo.updater']['solar_update_interval'],
            logger=logger,
            site_id=config['solar']['site_id'],
            solar_key=config['solar']['key'],
            lon=None,
            lat=None,
            height=None)

    @classmethod
    def tearDownClass(cls):
        cls.dbManager.remove_complete_database()
        cls.dbManager.disconnect()

    @classmethod
    def setUp(cls):
        cls.session = sessionmaker(bind=cls.connection)()

    @classmethod
    def tearDown(cls):
        cls.session.close()

    @staticmethod
    def load_energy_data(json_file):
        with open(json_file) as json_data:
            return json.load(json_data)

    def test_update_datetime_period_valid(self):
        json_period_data = self.load_energy_data('data/energy2019-06_quoter.json')

        when(self.updater).download_datetime_period(eq(datetime.strptime('1979-01-09', '%Y-%m-%d')),
                                                    eq(datetime.strptime('1989-01-09','%Y-%m-%d')))\
            .thenReturn(json_period_data)
        period = '1979-01-09:1989-01-09'
        self.updater.update_datetime_period(period)

    def test_update_datetime_period_invalid_both(self):
        period = 'xyzz-01-09:asdf-01-ipsum'
        with self.assertRaises(ValueError) as context:
            self.updater.update_datetime_period(period)

        self.assertTrue('does not match format' in str(context.exception))

    def test_update_datetime_period_invalid_from(self):
        period = 'xyzz-01-09:1979-01-09'
        with self.assertRaises(ValueError) as context:
            self.updater.update_datetime_period(period)

        self.assertTrue('does not match format' in str(context.exception))

    def test_update_datetime_period_invalid_to(self):
        period = '1979-01-09:qwer-ty-00'
        with self.assertRaises(ValueError) as context:
            self.updater.update_datetime_period(period)

        self.assertTrue('does not match format' in str(context.exception))

    def test_update_from_file(self):
        file_name = 'data/energy2019-06_quorter.json'
        self.updater.update_from_file(file_name)

    @classmethod
    def load_station_text_json(cls, file_name):
        with open(file_name) as json_file:
            return json.load(json_file)


