###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###


import unittest
import json

from tests import StationCommon, Config

from meteo_updater.meteo_updater import MeteoUpdater

from tests.SolarMeteoTestConfig import SolarMeteoTestConfig

IMGW_STATION_ID = 'id_stacji'

STATION1_FILE = '/tests/resources/station1.json'


class TestMeteoUpdater(unittest.TestCase):
    """
    Tests against MeteoUpdater
    """

    @classmethod
    def setUpClass(cls):
        cls.testconfig = SolarMeteoTestConfig()

        cls.meteo_db_url=cls.testconfig['meteo.database']['url']

        cls.updater = MeteoUpdater(
            meteo_db_url=cls.testconfig['meteo.database']['url'],
            meteo_data_url=cls.testconfig['imgw']['url'],
            updater_interval=cls.testconfig['meteo.updater']['imgw_update_interval'],
            updater_update_station_coordinates=True if cls.testconfig['imgw']['update_station_coordinates'] == 'yes' else False,
            updater_update_station_coordinates_file=cls.testconfig['imgw']['update_station_coordinates_file'],)

    @classmethod
    def setUp(cls):
        cls.session = cls.testconfig.create_session()
        cls.testconfig.init_complete_database()

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
        station_json = self.load_station_text_json(self.testconfig.SOLARMETEO_ROOT + STATION1_FILE)

        station = self.updater.save_station(self.session, station_json)
        self.session.commit()

        assert str(station.imgw_id) == str(station_json[IMGW_STATION_ID])

    def test_save_station_data(self):
        # given
        StationCommon.remove_all_stations(self.session)
        station_json = self.load_station_text_json(self.testconfig.SOLARMETEO_ROOT + STATION1_FILE)

        station = self.updater.save_station(self.session, station_json)
        self.session.commit()

        station_data = self.updater.save_station_data(self.session, station.id, station_json)
        self.session.commit()

        assert station_data.station_id == station.id

    def test_save_station_data_duplicate(self):
        StationCommon.remove_all_stations(self.session)
        station_json = self.load_station_text_json(self.testconfig.SOLARMETEO_ROOT + STATION1_FILE)

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
