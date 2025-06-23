###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

import configparser


def read_config():
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read('tests/resources/meteo_test.properties')
    return config
