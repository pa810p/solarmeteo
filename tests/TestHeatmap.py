import datetime
import unittest
import json
import tempfile
import os
import imageio.v3 as iio
from PIL import Image
import numpy as np

from solarmeteo.updater.meteo_updater import MeteoUpdater
from tests import StationCommon

from solarmeteo.heatmap.heatmap import HeatMap
from solarmeteo.heatmap.data_provider import DataProvider, TemperatureProvider
from tests.SolarMeteoTestConfig import SolarMeteoTestConfig


DEFAULT_HEATMAP_RANGES = {
    'temperature': (-5, 30),
    'pressure': (1000, 1030),
    'humidity': (0, 100),
    'wind': (0, 15),
    'precipitation': (0, 10),
    'pm10': (0, 40),
    'pm25': (0, 40),
}


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
        hm = HeatMap(
            meteo_db_url=self.meteo_db_url,
            last=2,
            heatmap_type='temperature',
            max_workers=1,
            file_format='cache',
            ranges=DEFAULT_HEATMAP_RANGES,
        )
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
        hm = HeatMap(
            meteo_db_url=self.meteo_db_url,
            last=1,
            heatmap_type='temperature',
            max_workers=1,
            output_file=output_filepath,
            file_format='png',
            usedb=False,
            persist=False,
            ranges=DEFAULT_HEATMAP_RANGES,
        )
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
        hm = HeatMap(
            meteo_db_url=self.meteo_db_url,
            last=1,
            heatmap_type='temperature',
            max_workers=1,
            output_file=output_filepath,
            file_format='png',
            usedb=False,
            persist=True,
            ranges=DEFAULT_HEATMAP_RANGES,
        )
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
        hm = HeatMap(
            meteo_db_url=self.meteo_db_url,
            last=2,
            heatmap_type='pressure',
            max_workers=2,
            output_file=output_filepath,
            file_format='gif',
            usedb=False,
            persist=True,
            ranges=DEFAULT_HEATMAP_RANGES,
        )
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
        hm = HeatMap(
            meteo_db_url=self.meteo_db_url,
            last=2,
            heatmap_type='humidity',
            max_workers=2,
            file_format='webp',
            usedb=False,
            persist=True,
            output_file=output_filepath1,
            ranges=DEFAULT_HEATMAP_RANGES,
        )
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


    def test_store_frames_overwrites_existing_entries(self):
        # given
        self.testconfig.init_complete_database()
        provider = TemperatureProvider(self.meteo_db_url, last=1)
        frame_datetime = datetime.datetime(2025, 1, 1, 12, 0, 0)
        first_frame = np.zeros((4, 4), dtype=np.uint8)
        updated_frame = np.full((4, 4), 255, dtype=np.uint8)

        # when - store initial frame
        provider.store_frames('temperature', {frame_datetime: first_frame})
        stored_once = provider.provide_frames_by_type_and_datetimes(datetimes=[frame_datetime])
        self.assertTrue(np.array_equal(stored_once[frame_datetime], first_frame))

        # when - store updated frame for same datetime
        provider.store_frames('temperature', {frame_datetime: updated_frame})

        # then - retrieved frame reflects updated data (overwrite succeeded)
        stored_twice = provider.provide_frames_by_type_and_datetimes(datetimes=[frame_datetime])
        self.assertTrue(np.array_equal(stored_twice[frame_datetime], updated_frame))


    def test_store_frames_creates_new_frame_type(self):
        # given
        self.testconfig.init_complete_database()
        provider = DataProvider(self.meteo_db_url, last=1)
        heatmap_name = 'custom_heatmap'
        frame_datetime = datetime.datetime(2025, 1, 2, 9, 0, 0)
        frame = np.full((3, 3), 7, dtype=np.uint8)

        # when - storing against a previously unknown heatmap
        provider.store_frames(heatmap_name, {frame_datetime: frame})

        # then - frame can be retrieved which implies FrameType was auto-created
        stored = provider.provide_frames_by_type_and_datetimes(heatmap=heatmap_name, datetimes=[frame_datetime])
        self.assertIn(frame_datetime, stored)
        self.assertTrue(np.array_equal(stored[frame_datetime], frame))


    def test_delete_older_than_datetimes_removes_nonlisted(self):
        # given
        self.testconfig.init_complete_database()
        provider = TemperatureProvider(self.meteo_db_url, last=1)
        datetimes = [
            datetime.datetime(2025, 1, 1, 12, 0, 0),
            datetime.datetime(2025, 1, 1, 13, 0, 0),
            datetime.datetime(2025, 1, 1, 14, 0, 0),
        ]
        frames = {dt: np.full((2, 2), idx, dtype=np.uint8) for idx, dt in enumerate(datetimes)}
        provider.store_frames('temperature', frames)

        # when
        removed = provider.delete_older_than_datetimes('temperature', [datetimes[1], datetimes[2]])

        # then
        self.assertEqual(1, removed)
        remaining = provider.provide_frames_by_type_and_datetimes(datetimes=datetimes)
        self.assertNotIn(datetimes[0], remaining)
        self.assertIn(datetimes[1], remaining)
        self.assertIn(datetimes[2], remaining)


    def test_delete_older_frames_keeps_latest_entries(self):
        # given
        self.prepare_database()
        provider = TemperatureProvider(self.meteo_db_url, last=1)
        datetimes = provider.get_last_datetimes(2)
        self.assertGreaterEqual(len(datetimes), 2)
        frames = {dt: np.full((3, 3), idx, dtype=np.uint8) for idx, dt in enumerate(datetimes)}
        provider.store_frames('temperature', frames)

        # when
        removed = provider.delete_older_frames('temperature', keep_frames=1)

        # then
        self.assertGreaterEqual(removed, 1)
        remaining = provider.provide_frames_by_type_and_datetimes(datetimes=datetimes)
        # delete_older_frames should keep the most recent datetime only
        latest_datetime = datetimes[0]
        older_datetime = datetimes[1]
        self.assertIn(latest_datetime, remaining)
        self.assertNotIn(older_datetime, remaining)


    def test_delete_older_frames_deletes_all_when_zero(self):
        # given
        self.testconfig.init_complete_database()
        provider = TemperatureProvider(self.meteo_db_url, last=1)
        datetimes = [
            datetime.datetime(2025, 1, 2, 10, 0, 0),
            datetime.datetime(2025, 1, 2, 11, 0, 0),
        ]
        frames = {dt: np.full((2, 2), idx, dtype=np.uint8) for idx, dt in enumerate(datetimes)}
        provider.store_frames('temperature', frames)

        # when
        removed = provider.delete_older_frames('temperature', keep_frames=0)

        # then
        self.assertEqual(len(datetimes), removed)
        remaining = provider.provide_frames_by_type_and_datetimes(datetimes=datetimes)
        self.assertEqual({}, remaining)


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
