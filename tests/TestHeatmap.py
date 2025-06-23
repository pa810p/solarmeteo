import unittest

from tests.DBManager import DBManager
from tests import StationCommon, Config
from sqlalchemy.orm import sessionmaker
from logger import logs

from heatmap.heatmap import HeatMap
from tests.SolarMeteoTestConfig import SolarMeteoTestConfig


class TestHeatMap(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        # cls.dbManager.init_complete_database()
        cls.testconfig = SolarMeteoTestConfig()

        cls.logger = logs.setup_custom_logger('heatmap', cls.testconfig['meteo']['loglevel'])
        cls.meteo_db_url=cls.testconfig['meteo.database']['url']



    @classmethod
    def setUp(cls):
        cls.session = cls.testconfig.create_session()
        cls.testconfig.init_complete_database()
        cls.logger.disabled = False


    @classmethod
    def tearDown(cls):
        cls.session.close()


    def test_create_frame_cache(self):
        StationCommon.import_stations(self.session, self.testconfig.SOLARMETEO_ROOT + '/tests/resources/station_list.txt')
        hm = HeatMap(meteo_db_url=self.meteo_db_url, last=1, heatmap_type='temperature', max_workers=1, file_format='cache')
        hm.generate()



if __name__ == '__main__':
    unittest.main()
