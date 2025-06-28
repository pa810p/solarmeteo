import datetime
import unittest
import json

from meteo_updater.meteo_updater import MeteoUpdater
from tests import StationCommon

from heatmap.heatmap import HeatMap
from tests.SolarMeteoTestConfig import SolarMeteoTestConfig


class TestHeatMap(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        cls.testconfig = SolarMeteoTestConfig()
        cls.meteo_db_url=cls.testconfig['meteo.database']['url']


    @classmethod
    def setUp(cls):
        cls.session = cls.testconfig.create_session()
        cls.testconfig.init_complete_database()


    @classmethod
    def tearDown(cls):
        cls.session.close()


    def test_create_frames_cache(self):
        # given
        StationCommon.import_stations(self.session, self.testconfig.SOLARMETEO_ROOT + '/tests/resources/station_list.csv')

        with open(self.testconfig.SOLARMETEO_ROOT + '/tests/resources/station_data.json', 'r') as f:
            station_data = json.loads(f.read())

        meteo_updater = self.create_updater()
        meteo_updater.update_stations(self.session, station_data, None)

        # when
        hm = HeatMap(meteo_db_url=self.meteo_db_url, last=2, heatmap_type='temperature', max_workers=1, file_format='cache')
        hm.generate()

        # then
        frames = hm.dataprovider.provide_frames_by_type_and_datetimes(heatmap='temperature', datetimes=['2025-06-23 17:00:00', '2025-06-23 18:00:00'])
        assert frames is not None
        assert len(frames) == 2
        assert frames[datetime.datetime(2025, 6, 23, 18, 0, 0)] is not None
        assert frames[datetime.datetime(2025, 6, 23, 17, 0, 0)] is not None


    @classmethod
    def create_updater(cls):
        return MeteoUpdater(
            meteo_db_url=cls.testconfig['meteo.database']['url'],
            meteo_data_url=cls.testconfig['imgw']['url'],
            updater_interval=cls.testconfig['meteo.updater']['imgw_update_interval'],
            updater_update_station_coordinates=True if cls.testconfig['imgw']['update_station_coordinates'] == 'yes' else False,
            updater_update_station_coordinates_file=cls.testconfig['imgw']['update_station_coordinates_file'])


if __name__ == '__main__':
    unittest.main()
