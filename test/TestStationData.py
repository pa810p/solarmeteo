###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

import unittest
from datetime import datetime

from sqlalchemy.orm import sessionmaker

from test import StationCommon
from test.StationCommon import create_station
from test.DBManager import DBManager
from model.station_data import StationData


class TestStationData(unittest.TestCase):

    dbManager = DBManager()

    @classmethod
    def setUpClass(cls):
        cls.dbManager.init_complete_database()
        cls.connection = cls.dbManager.connect()

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

    def testCreateStationData(self):

        StationCommon.remove_all_stations(self.session)

        station = create_station(self.session)

        station_data = StationData(station_id=station.id,
                                   datetime=datetime.now(),
                                   temperature=12.3,
                                   wind_speed=1.6,
                                   wind_direction=90.4,
                                   humidity=32.1,
                                   precipitation=52.4,
                                   pressure=1013.0)

        self.session.add(station_data)
        self.session.commit()

        result = self.session.query(StationData).filter_by(id=station_data.id).all()

        assert result[0].id == station_data.id
        assert len(result) == 1

    def testCreateStationData_none_station_id(self):

        with self.assertRaises(Exception) as context:
            StationData(station_id=None,
                        datetime=datetime.now(),
                        temperature=12.3,
                        wind_speed=1.6,
                        wind_direction=90.4,
                        humidity=32.1,
                        precipitation=52.4,
                        pressure=1013.0)

        self.assertTrue('no station_id' in str(context.exception))

    def testCreateStationData_unknown_station_id(self):

        StationCommon.remove_all_stations(self.session)

        with self.assertRaises(Exception) as context:
            station_data = StationData(station_id=-1,
                                       datetime=datetime.now(),
                                       temperature=12.3,
                                       wind_speed=1.6,
                                       wind_direction=90.4,
                                       humidity=32.1,
                                       precipitation=52.4,
                                       pressure=1013.0)
            self.session.add(station_data)
            self.session.commit()

        self.assertTrue('foreign key' in str(context.exception))

    def testCreateStationData_no_datetime(self):
        StationCommon.remove_all_stations(self.session)

        station = create_station(self.session)

        with self.assertRaises(Exception) as context:
            station_data = StationData(station_id=station.id,
                                       datetime=None,
                                       temperature=12.3,
                                       wind_speed=1.6,
                                       wind_direction=90.4,
                                       humidity=32.1,
                                       precipitation=52.4,
                                       pressure=1013.0)
            self.session.add(station_data)
            self.session.commit()

        self.assertTrue('no datetime' in str(context.exception))

    def testCreateStationData_exist_data(self):
        StationCommon.remove_all_stations(self.session)

        station = create_station(self.session)
        now = datetime.now()

        station_data = StationData(station_id=station.id,
                                   datetime=now,
                                   temperature=12.3,
                                   wind_speed=1.6,
                                   wind_direction=90.4,
                                   humidity=32.1,
                                   precipitation=52.4,
                                   pressure=1013.0)

        self.session.add(station_data)
        self.session.commit()

        station_data2 = StationData(station_id=station.id,
                                   datetime=now,
                                   temperature=12.3,
                                   wind_speed=1.6,
                                   wind_direction=90.4,
                                   humidity=32.1,
                                   precipitation=52.4,
                                   pressure=1013.0)
        with self.assertRaises(Exception) as context:
            self.session.add(station_data2)
            self.session.commit()

        self.assertTrue('duplicate key value violates unique constraint' in str(context.exception))


