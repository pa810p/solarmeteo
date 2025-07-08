import datetime
import unittest
import json
import tempfile
import os
import imageio.v3 as iio
from PIL import Image
import numpy as np

from solarmeteo.meteo_updater.meteo_updater import MeteoUpdater
from tests import StationCommon

from solarmeteo.heatmap.heatmap import HeatMap
from tests.SolarMeteoTestConfig import SolarMeteoTestConfig


class TestHeatMap(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        cls.testconfig = SolarMeteoTestConfig()
        cls.meteo_db_url=cls.testconfig['meteo.database']['url']


    @classmethod
    def setUp(cls):
        cls.session = cls.testconfig.create_session()
        cls.test_dir = tempfile.mkdtemp()

    @classmethod
    def tearDown(cls):
        cls.session.close()
        for file in os.listdir(cls.test_dir):
            os.remove(os.path.join(cls.test_dir, file))
        os.rmdir(cls.test_dir)


    def prepare_database(self):
        self.testconfig.init_complete_database()

        StationCommon.import_stations(self.session, self.testconfig.SOLARMETEO_ROOT + '/tests/resources/station_list.csv')
        with open(self.testconfig.SOLARMETEO_ROOT + '/tests/resources/station_data.json', 'r') as f:
            station_data = json.loads(f.read())
            meteo_updater = self.create_updater()
            meteo_updater.update_stations(self.session, station_data, None)


    def test_create_frames_cache(self):
        # given
        self.prepare_database()

        # when
        hm = HeatMap(meteo_db_url=self.meteo_db_url, last=2, heatmap_type='temperature', max_workers=1, file_format='cache')
        hm.generate()

        # then
        frames = hm.dataprovider.provide_frames_by_type_and_datetimes(datetimes=['2025-06-23 17:00:00', '2025-06-23 18:00:00'])
        self.assertIsNotNone(frames)
        self.assertEqual(2, len(frames))
        self.assertIsNotNone(frames[datetime.datetime(2025, 6, 23, 18, 0, 0)])
        self.assertIsNotNone(frames[datetime.datetime(2025, 6, 23, 17, 0, 0)])


    def test_create_png_not_persist(self):
        # given
        self.prepare_database()
        output_filepath = self.test_dir+'/temperature.png'

        # when
        hm = HeatMap(meteo_db_url=self.meteo_db_url, last=1, heatmap_type='temperature', max_workers=1,
                     output_file=output_filepath, file_format='png',
                     usedb=False, persist=False)
        hm.generate()
        frames = hm.dataprovider.provide_frames_by_type_and_datetimes(datetimes=['2025-06-23 17:00:00', '2025-06-23 18:00:00'])

        # then
        self.assertTrue(os.path.exists(output_filepath))
        self.assertIsInstance(iio.imread(output_filepath), np.ndarray)
        self.assertEqual(0, len(frames))


    def test_create_png_persist(self):
        # given
        self.prepare_database()
        output_filepath = self.test_dir+'/temperature.png'

        # when
        hm = HeatMap(meteo_db_url=self.meteo_db_url, last=1, heatmap_type='temperature', max_workers=1,
                     output_file=output_filepath, file_format='png',
                     usedb=False, persist=True)
        hm.generate()
        frames = hm.dataprovider.provide_frames_by_type_and_datetimes(datetimes=['2025-06-23 17:00:00', '2025-06-23 18:00:00'])

        # then
        self.assertTrue(os.path.exists(output_filepath))
        self.assertIsInstance(iio.imread(output_filepath), np.ndarray)
        self.assertEqual(1, len(frames))


    def test_create_animated_gif(self):
        # given
        self.prepare_database()
        output_filepath = self.test_dir+'/pressure.gif'

        # when
        hm = HeatMap(meteo_db_url=self.meteo_db_url, last=2, heatmap_type='pressure', max_workers=2,
             output_file=output_filepath, file_format='gif',
             usedb=False, persist=True)
        hm.generate()
        frames = hm.dataprovider.provide_frames_by_type_and_datetimes(datetimes=['2025-06-23 17:00:00', '2025-06-23 18:00:00'])

        # then
        self.assertTrue(os.path.exists(output_filepath))
        img = iio.imread(output_filepath)
        self.assertIsInstance(img, np.ndarray)
        self.assertEqual(2, img.shape[0])
        self.assertEqual(2, len(frames))


    def test_create_animated_webp_from_persistence(self):
        # given
        self.prepare_database()
        output_filepath1 = self.test_dir+'/humidity1.webp'
        output_filepath2 = self.test_dir+'/humidity2.webp'

        # when
        hm = HeatMap(meteo_db_url=self.meteo_db_url, last=2, heatmap_type='humidity', max_workers=2, file_format='webp',
                     usedb=False, persist=True, output_file=output_filepath1)
        hm.generate()
        frames = hm.dataprovider.provide_frames_by_type_and_datetimes(datetimes=['2025-06-23 17:00:00', '2025-06-23 18:00:00'])

        # then
        self.assertTrue(os.path.exists(output_filepath1))
        self.assertEqual(2, self.count_frames(output_filepath1))
        self.assertEqual(2, len(frames))

        # given
        hm.persist = False
        hm.usedb = True
        hm.output_file = output_filepath2
        hm.generate()

        self.assertTrue(os.path.exists(output_filepath2))
        img = iio.imread(output_filepath2)
        self.assertIsInstance(img, np.ndarray)
        self.assertEqual(2, self.count_frames(output_filepath1))


    @classmethod
    def create_updater(cls):
        return MeteoUpdater(
            meteo_db_url=cls.testconfig['meteo.database']['url'],
            meteo_data_url=cls.testconfig['imgw']['url'],
            updater_interval=cls.testconfig['meteo.updater']['imgw_update_interval'],
            updater_update_station_coordinates=True if cls.testconfig['imgw']['update_station_coordinates'] == 'yes' else False,
            updater_update_station_coordinates_file=cls.testconfig['imgw']['update_station_coordinates_file'])


    @classmethod
    def count_frames(cls, image_file_name):
        with Image.open(image_file_name) as im:
            count = 0
            try:
                while True:
                    im.seek(count)
                    count += 1
            except EOFError:
                pass
            return count

if __name__ == '__main__':
    unittest.main()
