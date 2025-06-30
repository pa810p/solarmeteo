###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

from solarmeteo.model.solar_data import SolarData


def remove_all_solar_data(session):
    session.query(SolarData).delete()
    session.commit()
