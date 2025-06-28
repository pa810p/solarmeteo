###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

from datetime import datetime, timedelta

import astropy.time
from astropy.coordinates import EarthLocation, AltAz, get_sun

import unittest

from meteo_updater import sun


class TestSun(unittest.TestCase):

    @unittest.skip("not implemented yet")
    def test_calculate_sun(self):
        sun.calculate_sun(
            datetime.now(),
            self.longitude,
            self.latitude,
            self.height
        )

