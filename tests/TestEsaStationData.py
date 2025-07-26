###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

import unittest
from datetime import datetime

from solarmeteo.model import EsaStation
from tests import StationCommon
from tests.SolarMeteoTestConfig import SolarMeteoTestConfig
from solarmeteo.model.esa_station_data import EsaStationData

from logging import getLogger

from tests.StationCommon import create_esa_station

logger = getLogger("solarupdater_tests")

class TestEsaStationData(unittest.TestCase):


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



    def testCreateEsaStationData(self):
        # given
        esa_station = create_esa_station(self.session)

        # when
        esa_station_data = EsaStationData(
            esa_station_id=esa_station.id,
            humidity=80,
            pressure=1013.12,
            temperature=22.2,
            pm10=5.5,
            pm25=7.0001,
            datetime='2025-07-26 10:20:11'
        )

        self.session.add(esa_station_data)
        self.session.commit()

        # then
        result = self.session.query(EsaStationData).filter_by(id=esa_station_data.id).all()

        assert result[0].id == esa_station_data.id
        assert len(result) == 1


    def testCreateStationData_none_station_id(self):
        # when
        with self.assertRaises(Exception) as context:
            EsaStationData(
                esa_station_id=None,
                humidity=80,
                pressure=1013.12,
                temperature=22.2,
                pm10=5.5,
                pm25=7.0001,
                datetime='2025-07-26 10:20:11'
            )

        # then
        self.assertTrue('no esa_station_id' in str(context.exception))


    def testCreateStationData_unknown_station_id(self):
        # when
        with self.assertRaises(Exception) as context:
            esa_station_data = EsaStationData(
                esa_station_id=-1,
                humidity=80,
                pressure=1013.12,
                temperature=22.2,
                pm10=5.5,
                pm25=7.0001,
                datetime='2025-07-26 10:20:11'
            )

            self.session.add(esa_station_data)
            self.session.commit()

        # then
        self.assertTrue('foreign key' in str(context.exception))


    def testCreateStationData_no_datetime(self):
        # given
        esa_station = create_esa_station(self.session)

        # when
        with self.assertRaises(Exception) as context:
            esa_station_data = EsaStationData(
                esa_station_id=esa_station.id,
                humidity=80,
                pressure=1013.12,
                temperature=22.2,
                pm10=5.5,
                pm25=7.0001,
                datetime=None
            )

            self.session.add(esa_station_data)
            self.session.commit()

        # then
        self.assertTrue('no datetime' in str(context.exception))

    def testCreateStationData_exist_data(self):
        # given
        esa_station = create_esa_station(self.session)
        now = datetime.now()

        esa_station_data = EsaStationData(
            esa_station_id=esa_station.id,
            humidity=80,
            pressure=1013.12,
            temperature=22.2,
            pm10=5.5,
            pm25=7.0001,
            datetime=now
        )

        self.session.add(esa_station_data)
        self.session.commit()

        esa_station_data2 = EsaStationData(
            esa_station_id=esa_station.id,
            humidity=80,
            pressure=1013.12,
            temperature=22.2,
            pm10=5.5,
            pm25=7.0001,
            datetime=now
        )

        # when
        with self.assertRaises(Exception) as context:
            self.session.add(esa_station_data2)
            self.session.commit()

        # then
        self.assertTrue('duplicate key value violates unique constraint' in str(context.exception))


