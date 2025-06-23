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

from logger import logs
from meteo_updater.solar_updater import SolarUpdater
from tests.DBManager import DBManager
from tests import StationCommon, Config
from tests.SolarMeteoTestConfig import SolarMeteoTestConfig

IMGW_STATION_ID = 'id_stacji'

STATION1_FILE = 'test/data/station1.json'


class TestSolarUpdater(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        cls.testconfig = SolarMeteoTestConfig()

        cls.logger = logs.setup_custom_logger('updater', cls.testconfig['meteo']['loglevel'])
        cls.meteo_db_url=cls.testconfig['meteo.database']['url']

        cls.updater = SolarUpdater(
            meteo_db_url=cls.testconfig['meteo.database']['url'],
            data_url=cls.testconfig['solar']['url'],
            updater_interval=cls.testconfig['meteo.updater']['solar_update_interval'],
            logger=cls.testconfig,
            site_id=cls.testconfig['solar']['site_id'],
            solar_key=cls.testconfig['solar']['key'],
            lon=None,
            lat=None,
            height=None)

    @classmethod
    def setUp(cls):
        cls.session = cls.testconfig.create_session()
        cls.testconfig.init_complete_database()
        cls.logger.disabled = False

    @classmethod
    def tearDown(cls):
        cls.session.close()


    @staticmethod
    def load_energy_data(json_file):
        with open(json_file) as json_data:
            return json.load(json_data)
    #
    # def test_update_datetime_period_valid(self):
    #     json_period_data = self.load_energy_data(self.testconfig.SOLARMETEO_ROOT + '/tests/resources/energy2019-06_quoter.json')
    #
    #     when(self.updater).download_datetime_period(eq(datetime.strptime('1979-01-09', '%Y-%m-%d')),
    #                                                 eq(datetime.strptime('1989-01-09','%Y-%m-%d')))\
    #         .thenReturn(json_period_data)
    #     period = '1979-01-09:1989-01-09'
    #     self.updater.update_datetime_period(period)

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

    # def test_update_from_file(self):
    #     file_name = self.testconfig.SOLARMETEO_ROOT + '/tests/resources/energy2019-06_quorter.json'
    #     self.updater.update_from_file(file_name)

    @classmethod
    def load_station_text_json(cls, file_name):
        with open(file_name) as json_file:
            return json.load(json_file)


