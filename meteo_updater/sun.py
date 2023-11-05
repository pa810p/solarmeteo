###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###


from astropy.coordinates import EarthLocation, AltAz, get_sun


def calculate_sun(datetime, lon, lat, masl):
    loc = EarthLocation.from_geodetic(lon, lat, masl)
    altaz = AltAz(obstime=datetime, location=loc)
    angle = get_sun(datetime).transform_to(altaz)

    print(angle.az.degree)
    print(angle.alt.degree)

    return angle.az.degree, angle.alt.degree

