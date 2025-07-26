###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###
from psycopg2 import IntegrityError

from solarmeteo.model import EsaStation
from solarmeteo.model.station import Station

IMGW_ID = 123456


def create_station(session):
    name = 'station_name'
    longitude = 123.55
    latitude = 123.112

    station = Station(name, IMGW_ID, longitude, latitude)

    session.add(station)
    session.commit()

    return station

def create_esa_station(session):
    esa_station = EsaStation(
        name='Station name',
        street='Street name',
        post_code='12-321',
        city='Miami',
        longitude='12.3211',
        latitude='54.21232'
    )

    #when
    session.add(esa_station)
    session.commit()

    return esa_station

def import_stations(session, filepath):
    count = 0
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                imgw_id, name, lat, lon = line.split(',')
                station = Station(
                    imgw_id=int(imgw_id),
                    name=name,
                    lat=float(lat),
                    lon=float(lon)
                )
                session.add(station)
                session.commit()
                count += 1
            except (ValueError, IntegrityError):
                session.rollback()
                continue

    return count


def remove_all_stations(session):
    session.query(Station).delete()
    session.commit()


def remove_all_esa_stations(session):
    session.query(EsaStation).delete()
    session.commit()

