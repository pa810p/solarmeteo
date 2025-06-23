###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

import unittest

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from logger import logs
from tests import StationCommon
from tests.DBManager import DBManager
from tests.SolarMeteoTestConfig import SolarMeteoTestConfig
from tests.StationCommon import create_station
from model.station import Station


class TestStation(unittest.TestCase):


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
        updater = None


    def test_CreateStation(self):

        StationCommon.remove_all_stations(self.session)

        station = create_station(self.session)

        result = self.session.query(Station).filter_by(id=station.id).all()

        assert result[0].id == station.id
        assert len(result) == 1

    def test_CreateStation_nonename(self):
        name = None
        imgw_id = 123456
        longitude = 123.55
        latitude = 123.112

        with self.assertRaises(Exception) as context:
            Station(name, imgw_id, longitude, latitude)
        self.assertTrue('no name' in str(context.exception))

    def test_CreateStation_noname(self):
        name = ''
        imgw_id = 123456
        longitude = 123.55
        latitude = 123.112

        with self.assertRaises(Exception) as context:
            Station(name, imgw_id, longitude, latitude)
        self.assertTrue('no name' in str(context.exception))

    def test_CreateStation_noIMGWID(self):
        name = 'station'
        imgw_id = None
        longitude = 123.55
        latitude = 123.112

        with self.assertRaises(Exception) as context:
            Station(name, imgw_id, longitude, latitude)
        self.assertTrue('no IMGW id' in str(context.exception))

    def test_CreateStations_duplicateIMGWID(self):
        longitude = 123.55
        latitude = 123.112

        StationCommon.remove_all_stations(self.session)

        station1 = Station('First', 123, longitude, latitude)

        self.session.add(station1)
        self.session.commit()

        station2 = Station('Second', 123, longitude, latitude)

        with self.assertRaises(sqlalchemy.exc.IntegrityError) as context:
            self.session.add(station2)
            self.session.commit()

        self.assertTrue('duplicate key value' in str(context.exception))