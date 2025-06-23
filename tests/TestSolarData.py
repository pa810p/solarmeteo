###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

import unittest
from datetime import datetime

from sqlalchemy.orm import sessionmaker

from logger import logs
from model.solar_data import SolarData
from tests import SolarCommon
from tests.DBManager import DBManager
from tests.SolarMeteoTestConfig import SolarMeteoTestConfig


class TestSolarData(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        cls.testconfig = SolarMeteoTestConfig()

        cls.logger = logs.setup_custom_logger('updater', cls.testconfig['meteo']['loglevel'])
        cls.meteo_db_url=cls.testconfig['meteo.database']['url']


    @classmethod
    def setUp(cls):
        cls.session = cls.testconfig.create_session()
        cls.testconfig.init_complete_database()
        cls.logger.disabled = False

    @classmethod
    def tearDown(cls):
        cls.session.close()


    def test_createSolarData(self):
        SolarCommon.remove_all_solar_data(self.session)

        now = datetime.now()
        solar_data = SolarData(now, 123.1)

        self.session.add(solar_data)
        self.session.commit()

        result = self.session.query(SolarData).filter_by(datetime=now).all()

        assert result[0].id == solar_data.id
        assert len(result) == 1

    def test_createSolarDataNoDatetime(self):
        with self.assertRaises(Exception) as context:
            SolarData(None, 123.1)

        self.assertTrue('no datetime' in str(context.exception))

    def test_createSolarDataNoValue(self):
        with self.assertRaises(Exception) as context:
            SolarData(datetime.now(), None)

        self.assertTrue('no power data' in str(context.exception))

    def test_createSolarDataDuplicateDatetime(self):
        now = datetime.now()
        solar_data = SolarData(now, 123.1)

        self.session.add(solar_data)
        self.session.commit()

        result = self.session.query(SolarData).filter_by(datetime=solar_data.datetime).all()

        assert result[0].id == solar_data.id
        assert len(result) == 1

        solar_data2 = SolarData(now, 123.1)

        with self.assertRaises(Exception) as context:
            self.session.add(solar_data2)
            self.session.commit()

        self.assertTrue('duplicate key' in str(context.exception))

