###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###


import configparser
import logging
import optparse

from solarmeteo.heatmap.heatmap import HeatMap
from solarmeteo.logger.logs import get_log_level, setup_logging
from solarmeteo.updater.esa_updater import EsaUpdater
from solarmeteo.updater.gios_updater import GiosUpdater
from solarmeteo.updater.meteo_updater import MeteoUpdater
from solarmeteo.updater.solar_updater import SolarUpdater


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
    heatmap = None
    output_file = None
    max_workers = 2
    last_hours = 1
    keep_frames = 72
    generate_frames = False
    generate_cache = False
    persist = False
    usedb = False
    gios_url = config['gios']['url']
    gios_stations = False
    gios_max_delay_sec = int(config['gios']['max_delay_sec'])
    esa_url = config['esa']['url']

    # and now overwrite them with command line if exists
    parser = optparse.OptionParser(usage="%prog [-b] [-m] [-i] [-f] [-l] [-o]", version=ver, description=desc)

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
    parser.add_option('--heatmap', dest='heatmap', help='generate map of: temperature, precipitation, humidity, pressure, windspeed')
    parser.add_option('--last-hours', dest='last_hours', help='generate animated map from last n hours', type=int, default=1)
    parser.add_option('--format', dest='file_format', help='file format for heatmap: png, gif (animated), default is png', default='png')
    parser.add_option('-o', '--output', dest='output_file', help='output file for heatmap, default is [heatmap].[png|gif]')
    parser.add_option('--max-workers', dest='max_workers', help='workers used in parallel when generating animations', type=int, default=2)
    parser.add_option('--progress', dest='progress', help='when generating heatmap indicates progressbar', action='store_true')
    parser.add_option('--generate-frames', dest='generate_frames', help='generate frames after meteo update', action='store_true')
    parser.add_option('--generate-cache', dest='generate_cache', help='generate cache for --last-hours station data', action='store_true')
    parser.add_option('--overwrite', dest='overwrite', help='cached frame will be overwritten with generated one', action='store_true')
    parser.add_option('--persist', dest='persist', help='persist frames in database', action='store_true')
    parser.add_option('--usedb', dest='usedb', help='use database persisted frames if available', action='store_true')
    parser.add_option("--gios-stations", dest="gios_stations", help="update gios stations database", action='store_true')

    # option not in properties
    # TODO: check if default can be set if empty in here
    parser.add_option('-u', '--update', dest='update', help='service to update [imgw, solar, gios], default is all')

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

    if options.heatmap is not None and not '' and len(options.heatmap) != 0:
        heatmap = options.heatmap

    if options.last_hours is not None and not '':
        last_hours = options.last_hours

    if options.file_format is not None and not '' and len(options.file_format) != 0:
        file_format = options.file_format

    if options.output_file is not None and not '' and len(options.output_file) != 0:
        output_file = options.output_file

    if options.max_workers is not None and not '':
        max_workers = options.max_workers

    if options.generate_frames is not None and not '':
        generate_frames = options.generate_frames

    if options.generate_cache is not None and not '':
        generate_cache = options.generate_cache

    if options.overwrite is not None and not '':
        overwrite = options.overwrite

    if options.persist is not None and not '':
        persist = options.persist

    if options.usedb is not None and not '':
        usedb = options.usedb

    if options.gios_stations is not None and not '':
        gios_stations = options.gios_stations

    setup_logging(level=get_log_level(log_level), project_prefix="solarmeteo")
    logger = logging.getLogger("solarmeteo.*")
    logger.info(f"Starting Solarmeteo...")

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
    if update == 'all' or update == 'imgw':
        imgw_updater = MeteoUpdater(
            meteo_db_url=meteo_db_url,
            meteo_data_url=imgw_data_url,
            updater_interval=imgw_update_interval,
            updater_update_station_coordinates=updater_update_station_coordinates,
            updater_update_station_coordinates_file=updater_update_station_coordinates_file)
        imgw_updater.update()

        if generate_frames:
            for frametype in HeatMap.heatmaps:
                hm = HeatMap(meteo_db_url=meteo_db_url, last=1, heatmap_type=frametype, max_workers=max_workers)
                hm.persist_frame()

    if update == 'all' or update == 'solar':
        solar_updater = SolarUpdater(
            meteo_db_url=meteo_db_url,
            data_url=solar_url,
            updater_interval=solar_update_interval,
            site_id=site_id,
            solar_key=solar_key,
            lon=lon,
            lat=lat,
            height=height)

        if solar_update_period is not None:
            solar_updater.update_datetime_period(solar_update_period)
        else:
            solar_updater.update()

    if update == 'all' or update == 'gios':
        gios_updater = GiosUpdater(meteo_db_url=meteo_db_url, gios_url=gios_url, max_delay_sec=gios_max_delay_sec)
        gios_updater.update_all_stations_data()

    if update == 'all' or update == 'esa':
        esa_updater = EsaUpdater(meteo_db_url=meteo_db_url, esa_data_url=esa_url)
        esa_updater.update()

    if heatmap is not None:
        if output_file is None:
            output_file = heatmap

        hm = HeatMap(meteo_db_url=meteo_db_url, last=last_hours, file_format=file_format,
                     output_file=output_file, heatmap_type=heatmap, max_workers=max_workers,
                     persist=persist, usedb=usedb)
        hm.generate()

    if generate_cache:
        for frametype in HeatMap.heatmaps:
            hm = HeatMap(meteo_db_url=meteo_db_url, last=last_hours, heatmap_type=frametype, max_workers=max_workers,
                         file_format='cache')
            hm.generate()

    if gios_stations:
        gios_updater = GiosUpdater(meteo_db_url=meteo_db_url, gios_url=gios_url)
        gios_updater.update_stations()


if __name__ == '__main__':
    desc = """This is a meteo analyzer"""
    ver = "%prog 2.0 (c) 2019-2025 Pawel Prokop"

    main()


