###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

import unittest

import sqlalchemy

from solarmeteo.model import EsaStation
from tests import StationCommon
from tests.SolarMeteoTestConfig import SolarMeteoTestConfig
from tests.StationCommon import create_station
from solarmeteo.model.station import Station


class TestEsaStation(unittest.TestCase):


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
        updater = None


    def test_CreateEsaStation(self):
        #given
        esa_station = EsaStation(
            name='Station name',
            street='Street name',
            post_code='12-321',
            city='Miami',
            longitude='12.3211',
            latitude='54.21232'
        )

        #when
        self.session.add(esa_station)
        self.session.commit()

        #then
        result = self.session.query(EsaStation).filter_by(id=esa_station.id).all()

        assert result[0].id == esa_station.id
        assert len(result) == 1

