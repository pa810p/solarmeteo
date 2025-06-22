###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###


import unittest
import json

from test.DBManager import DBManager
from test import StationCommon, Config
from sqlalchemy.orm import sessionmaker

from meteo_updater.meteo_updater import MeteoUpdater

from logger import logs

IMGW_STATION_ID = 'id_stacji'

STATION1_FILE = 'test/data/station1.json'


class TestMeteoUpdater(unittest.TestCase):
    """
    Tests against MeteoUpdater
    """

    dbManager = DBManager()

    updater = None

    @classmethod
    def setUpClass(cls):
        cls.dbManager.init_complete_database()
        cls.connection = cls.dbManager.connect()

        config = Config.read_config()

        logger = logs.setup_custom_logger('updater', config['meteo']['loglevel'])

        cls.updater = MeteoUpdater(
            meteo_db_url=config['meteo.database']['url'],
            meteo_data_url=config['imgw']['url'],
            updater_interval=config['meteo.updater']['imgw_update_interval'],
            updater_update_station_coordinates=True if config['imgw']['update_station_coordinates'] == 'yes' else False,
            updater_update_station_coordinates_file=config['imgw']['update_station_coordinates_file'],
            logger=logger)

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

    def test_find_station_by_imgw_id(self):
        StationCommon.remove_all_stations(self.session)

        station = StationCommon.create_station(self.session)
        result = self.updater.find_station_by_imgw_id(self.session, station.imgw_id)

        assert result.id == station.id
        assert result.imgw_id == station.imgw_id

    def test_find_station_by_imgw_id_unknown(self):
        StationCommon.remove_all_stations(self.session)

        result = self.updater.find_station_by_imgw_id(self.session, 666)

        assert result is None

    def test_save_station(self):
        StationCommon.remove_all_stations(self.session)
        station_json = self.load_station_text_json(STATION1_FILE)

        station = self.updater.save_station(self.session, station_json)
        self.session.commit()

        assert str(station.imgw_id) == str(station_json[IMGW_STATION_ID])

    def test_save_station_data(self):
        StationCommon.remove_all_stations(self.session)
        station_json = self.load_station_text_json(STATION1_FILE)

        station = self.updater.save_station(self.session, station_json)
        self.session.commit()

        station_data = self.updater.save_station_data(self.session, station.id, station_json)
        self.session.commit()

        assert station_data.station_id == station.id

    def test_save_station_data_duplicate(self):
        StationCommon.remove_all_stations(self.session)
        station_json = self.load_station_text_json(STATION1_FILE)

        station = self.updater.save_station(self.session, station_json)
        self.session.commit()

        self.updater.save_station_data(self.session, station.id, station_json)
        self.session.commit()

        # saving the same station data
        with self.assertRaises(Exception) as context:
            self.updater.save_station_data(self.session, station.id, station_json)
            self.session.commit()
        self.assertTrue('duplicate key value violates unique constraint' in str(context.exception))

    @classmethod
    def load_station_text_json(cls, station_file):
        with open(station_file, encoding='utf-8') as json_file:
            return json.load(json_file)
