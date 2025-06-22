###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###


import time
from datetime import datetime, timedelta
from model.station_data import StationData, IMGW_DATE, IMGW_HOUR, IMGW_TEMPERATURE, IMGW_WIND_SPEED, \
    IMGW_WIND_DIRECTION, IMGW_HUMIDITY, IMGW_PRECIPITATION, IMGW_PRESSURE
from model.station import Station, IMGW_STATION_ID, IMGW_STATION_NAME
from meteo_updater.updater import Updater

from logging import getLogger

import sqlalchemy.exc

logger = getLogger("updater")

class MeteoUpdater (Updater):
    """
    Downloads IMGW station data and stores it into a configured SQL database for further analyzes
    """
    def __init__(self, meteo_db_url, meteo_data_url, updater_interval, updater_update_station_coordinates,
                 updater_update_station_coordinates_file, logger):
        super(MeteoUpdater, self).__init__(meteo_db_url, updater_interval, logger)

        self.meteo_data_url = meteo_data_url
        self.updater_update_station_coordinates = updater_update_station_coordinates
        self.updater_update_station_coordinates_file = updater_update_station_coordinates_file

    def find_station_by_imgw_id(self, session, imgw_station_id):
        """
        Returns station from database by given imgw station id
        :param session database session
        :param imgw_station_id id of imgw station
        :return station
        """
        result = session.query(Station).filter_by(imgw_id=int(imgw_station_id)).all()
        if len(result) > 1:
            # this shouldn't happen due to database constraints
            logger.error(f'Too many records for station id: {imgw_station_id} returning first')
            raise Exception('Database has more than one imgw id')

        if len(result) == 1:
            return result[0]

        logger.error(f'station not found id: {imgw_station_id}')
        return None

    def save_station(self, session, station_json):
        """
        Stores new station to database.
        :param session database session
        :param station_json station information as json object
        """
        station = Station(name=station_json[IMGW_STATION_NAME],
                                  imgw_id=int(station_json[IMGW_STATION_ID])
                                  )
        logger.info('Attempting to create new station: %s' % station)
        session.add(station)
        return station

    def save_station_data(self, session, station_id, station_json):
        """
        Saves meteorogical data of a station
        """
        logger.debug('Saving station data')
        # Update station meteorology data
        station_data = StationData(station_id,
                                               self.create_datetime(station_json[IMGW_DATE],
                                                                    station_json[IMGW_HOUR]),
                                               station_json[IMGW_TEMPERATURE],
                                               station_json[IMGW_WIND_SPEED],
                                               station_json[IMGW_WIND_DIRECTION],
                                               station_json[IMGW_HUMIDITY],
                                               station_json[IMGW_PRECIPITATION],
                                               station_json[IMGW_PRESSURE])

        session.add(station_data)
        return station_data

    def read_coordinates(self):
        """
        Returns station coordination information from configured file
        :return list of tuples: station id, station lat, station lon
        """
        logger.debug(f'Getting coordinates data from a file: {self.updater_update_station_coordinates_file}')

        station_coordinates = []

        with open(self.updater_update_station_coordinates_file, encoding='utf-8') as stations:
            for station in stations:
                tokens = station.split(',')
                station_id = tokens[0].strip()
                station_lat = tokens[2].strip()
                station_lon = tokens[3].strip()

                if station_id is None or station_lon is None or station_lat is None:
                    self.logger.error(f'Invalid station data: station id=%s, station lat=%s, station lon={(station_id, station_lat, station_lon)}')
                else:
                    station_coordinates.append((float(station_id), float(station_lat), float(station_lon)))

        return station_coordinates

    @staticmethod
    def find_station_coordinates(imgw_id, coordinates):
        for coords in coordinates:
            if coords[0] == imgw_id:
                return coords[2], coords[1]
        return None, None

    @staticmethod
    def create_datetime(date, time):
        return datetime.strptime(date, '%Y-%m-%d') + timedelta(hours=int(time))

    def update_station(self, session, station, station_json, coordinates):
        """
        Rpdates station (if it's not recognized in the system) and station data
        :param session database session
        :param station station obcject
        :param station_json whole station_data object that contains station data and conditions
        :param coordinates station coordinates that have been read from external configuration file
        """
        if station is None:
            station = self.save_station(session, station_json)
            session.commit()
            logger.info('Created new station %r' % station)
        else:
            logger.debug('Got station: %r' % station)

        if self.updater_update_station_coordinates:
            logger.debug('Will update station coordinates')
            (lon, lat) = self.find_station_coordinates(station.imgw_id, coordinates)
            if lon is not None and lat is not None:
                self.logger.debug('Update coordinates.')
                station.longitude = lon
                station.latitude = lat
                session.commit()
        try:
            self.save_station_data(session, station.id, station_json)
            logger.debug('Commit station info')
            session.commit()
        except sqlalchemy.exc.IntegrityError as exception:
            # it's a common error because third party meteo stations do not upgrade server regularly
            logger.warning('StationData IntegrityError: %s' % exception.orig)
            session.rollback()
        except Exception as exception:
            logger.error('StationData error: %s' % exception)
            session.rollback()

    def update_stations(self, session, stations_json, coordinates):
        """
        Updates station_data for stations downloaded from imgw site
        :param session database session
        :param stations_json json format string for all stations to update
        :param coordinates station coordinates that have been read from external configuration file
        """
        for station_json in stations_json:
            station = self.find_station_by_imgw_id(session, station_json[IMGW_STATION_ID])
            self.update_station(session, station, station_json, coordinates)

    def update(self):
        """
        This is main update method that reads station coordinates, downloads data for all stations from external
        configured in properties file or command line parameters
        TODO: This method is not UNIT TESTED!
        """
        logger.info('IMGW Updating')

        coordinates = None
        if self.updater_update_station_coordinates:
            coordinates = self.read_coordinates()

        session = self.create_session()
        stations_json = self.get(self.meteo_data_url)
        logger.info('Received %s stations.' % str(len(stations_json)))

        self.update_stations(session, stations_json, coordinates)

        logger.debug('Closing connections')
        session.close_all()

    def update_daemonize(self):
        """
        This method is a wrapper for update method, it will periodically call update method as configured in
        properties or command line parameters
        TODO: This method is not UNIT TESTED!
        """
        while True:
            logger.info('IMGW will update as a daemon')
            self.update()

            logger.debug(f'IMGW is going to sleep for {self.updater_interval} seconds')
            time.sleep(int(self.updater_interval))
