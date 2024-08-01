###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###


import configparser
import optparse

from logs import logs
from meteo_updater import MeteoUpdater, SolarUpdater
import threading

# logger = logs.setup_custom_logger('main', 'DEBUG')


def main():
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read('meteo.properties')

    solar_update_period = None

    meteo_db_url = config['meteo.database']['url']
    log_level = config['meteo']['loglevel']
    # meteo_daemonize = config['meteo.updater']['daemoinize'] == 'True'

    imgw_data_url = config['imgw']['url']
    imgw_update_interval = config['meteo.updater']['imgw_update_interval']
    updater_update_station_coordinates = True if config['imgw']['update_station_coordinates'] == 'yes' else \
        False
    updater_update_station_coordinates_file = config['imgw']['update_station_coordinates_file']
    solar_key = config['solar']['key']
    site_id = config['solar']['site_id']
    lon = config['solar']['longitude']
    lat = config['solar']['latitude']
    height = config['solar']['height']
    solar_url = config['solar']['url']
    solar_update_interval = config['meteo.updater']['solar_update_interval']
    # TODO: this will be a coma separated list
    update = config['meteo.updater']['modules']

    # and now overwrite them with command line if exists
    parser = optparse.OptionParser(usage="%prog [-b] [-m] [-i] [-f] [-l]", version=ver, description=desc)

    # parser.add_option('-d', '--daemonize', dest='daemonize', action='store_true', default=False,
    #                   help='run as daemon process')
    parser.add_option('-b', '--database', dest='meteo_db_url', help='database connection string')
    parser.add_option('-m', '--meteo_data', dest='imgw_data_url', help='imgw data url')
    parser.add_option('-i', '--imgw_update_interval', dest='imgw_update_interval',
                      help='imgw update interval in daemonize mode')
    # parser.add_option('-s', '--solar_update_interval', dest='solar_update_interval',
    #                   help='solar update interval in daemonize mode')
    parser.add_option('-f', '--coordinates-file', dest='updater_update_station_coordinates_file',
                      help='file with station coordinates')
    parser.add_option('-c', '--update-coordinates', dest='updater_update_station_coordinates', action='store_true',
                      help='update station coordinates')
    parser.add_option('-l', '--log-level', dest='log_level', help='logging level')
    parser.add_option('-k', '--solar_key', dest='solar_key', help='solar key')
    parser.add_option('--site_id', dest='site_id', help='solar site id')
    parser.add_option('--longitude', dest='lon')
    parser.add_option('--latitude', dest='lat')
    parser.add_option('--height', dest='height')
    parser.add_option('--solar_url', dest='solar_url', help='solar base url')
    parser.add_option('--solar_update_interval', dest='solar_update_interval', help='solar update interval')
    parser.add_option('--solar-period', dest='solar_update_period', help='solar update from_date:to_date')

    # option not in properties
    # TODO: check if default can be set if empty in here
    parser.add_option('-u', '--update', dest='update', help='service to update [imgw, solar], default is both')

    (options, args) = parser.parse_args()

    # if options.daemonize is not None and not '':
    #     meteo_daemonize = options.daemonize

    if options.meteo_db_url is not None and not '' and len(options.meteo_db_url) != 0:
        meteo_db_url = options.meteo_db_url

    if options.imgw_data_url is not None and not '' and len(options.imgw_data_url) != 0:
        imgw_data_url = options.imgw_data_url

    if options.imgw_update_interval is not None and not '' and len(options.imgw_update_interval) != 0:
        imgw_update_interval = options.update_interval

    if options.updater_update_station_coordinates_file is not None and not '' and \
            len(options.updater_update_station_coordinates_file) != 0:
        updater_update_station_coordinates_file = options.updater_update_station_coordinates_file
        updater_update_station_coordinates = True

    if options.log_level is not None and not '' and len(options.log_level) != 0:
        log_level = options.log_level

    if options.update is not None and not '' and len(options.update) != 0:
        update = options.update
    # else:
    #     update = 'both'

    if options.solar_key is not None and not '' and len(options.solar_key) != 0:
        solar_key = options.solar_key

    if options.site_id is not None and not '' and len(options.site_id) != 0:
        site_id = options.site_id

    if options.lon is not None and not '' and len(options.lon) != 0:
        lon = options.lon

    if options.lat is not None and not '' and len(options.lat) != 0:
        lat = options.lat

    if options.height is not None and not '' and len(options.height) != 0:
        height = options.height

    if options.solar_url is not None and not '' and len(options.solar_url) != 0:
        solar_url = options.solar_url

    if options.solar_update_interval is not None and not '' and len(options.solar_update_interval) != 0:
        solar_update_interval = options.solar_update_interval

    logger = logs.setup_custom_logger('updater', log_level)

    imgw_updater = MeteoUpdater.MeteoUpdater(
        meteo_db_url=meteo_db_url,
        meteo_data_url=imgw_data_url,
        updater_interval=imgw_update_interval,
        updater_update_station_coordinates=updater_update_station_coordinates,
        updater_update_station_coordinates_file=updater_update_station_coordinates_file,
        logger=logger)

    solar_updater = SolarUpdater.SolarUpdater(
        meteo_db_url=meteo_db_url,
        data_url=solar_url,
        updater_interval=solar_update_interval,
        site_id=site_id,
        solar_key=solar_key,
        lon=lon,
        lat=lat,
        height=height,
        logger=logger)

    # if meteo_daemonize:
    #     try:
    #         logger.info('Go to daemonize mode')
    #         if update == 'both' or update == 'imgw':
    #             th_imgw_updater = threading.Thread(imgw_updater.update_daemonize())
    #             th_imgw_updater.daemon = True
    #             th_imgw_updater.start()  # it blocks
    #         # it will not be called
    #         if update == 'both' or update == 'solar':
    #             th_solar_updater = threading.Thread(solar_updater.update_daemonize())
    #             th_solar_updater.daemon = True
    #             th_solar_updater.start()
    #     except KeyboardInterrupt:
    #         logger.info('Main: Keyboard interrupt caught, terminating updates.')
    #         logger.info('Goodbye.')
    # else:

    # TODO: should be a list imgw, solar, something, all
    if update == 'both' or update == 'imgw':
        imgw_updater.update()
    if update == 'both' or update == 'solar':
        solar_updater.update()
    if solar_update_period is not None:
        solar_updater.update_datetime_period(solar_update_period)


if __name__ == '__main__':
    desc = """This is a meteo analyzer"""
    ver = "%prog 2.0 (c) 2019-2024 Pawel Prokop"

    main()
