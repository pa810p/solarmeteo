###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

from datetime import datetime, timedelta

import astropy.time
from astropy.coordinates import EarthLocation, AltAz, get_sun

import unittest


class TestSun(unittest.TestCase):

    longitude = 19.97
    latitude = 49.98
    height = 298

    home_azimuth = 180 - 28
    home_angle = 35
    # tan... 8.71 / 12.58
    home_azimuth_error = 1
    home_angle_error = 1

    def test_calculate(self):
        start_date = datetime.fromisoformat("2021-01-01 00:00:00")

        loc = EarthLocation.from_geodetic(self.longitude, self.latitude, self.height)
        altaz = AltAz(location=loc)

        for hour in range(0, 365 * 24):
            sun_datetime = start_date + timedelta(hours=hour)
            sun = get_sun(
                astropy.time.Time(
                    sun_datetime.strftime("%Y-%m-%dT%H:%M:%S"))).transform_to(altaz)

            sun_azimuth = float(sun.az.degree)
            sun_altitude = float(sun.alt.degree)
            azimuth_diff = abs(self.home_azimuth - sun_azimuth)
            alt_diff = abs(self.home_angle - sun_altitude)

            if azimuth_diff < self.home_azimuth_error and alt_diff < abs(self.home_angle_error):
                print("datetime=%s azimuth_diff=%f alt_diff=%f sun_azimuth=%f sun_altitude=%f" % (sun_datetime,
                                                                                                  azimuth_diff,
                                                                                                  alt_diff,
                                                                                                  sun_azimuth,
                                                                                                  sun_altitude))


