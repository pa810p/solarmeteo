###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

from meteo_updater.Station import Station

IMGW_ID = 123456


def create_station(session):
    name = 'station_name'
    longitude = 123.55
    latitude = 123.112

    station = Station(name, IMGW_ID, longitude, latitude)

    session.add(station)
    session.commit()

    return station


def remove_all_stations(session):
    session.query(Station).delete()
    session.commit()

