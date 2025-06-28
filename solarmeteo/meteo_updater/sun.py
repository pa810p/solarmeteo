###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###
import pytz
import astropy
from astropy.coordinates import EarthLocation, AltAz, get_sun


def calculate_sun(solar_datetime, lon, lat, height):
    loc = EarthLocation.from_geodetic(lon, lat, height)
    altaz = AltAz(location=loc)

    sunpos = get_sun(
        astropy.time.Time(
            solar_datetime
            .astimezone(pytz.utc)
            .strftime("%Y-%m-%dT%H:%M:%S")
                )).transform_to(altaz)

    sun_azimuth = float(sunpos.az.degree)
    sun_altitude = float(sunpos.alt.degree)

    return sun_azimuth, sun_altitude

