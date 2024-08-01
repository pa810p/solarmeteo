###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

from datetime import time, datetime

from sqlalchemy.orm import Session

from meteo_updater import sun
from meteo_updater.SolarData import SolarData
from meteo_updater.Updater import Updater
from meteo_updater.SunData import SunData


class SolarUpdater(Updater):
    def __init__(self, meteo_db_url, data_url, updater_interval, site_id, solar_key, lon, lat, height, logger):
        super(SolarUpdater, self).__init__(meteo_db_url, updater_interval, logger)
        self.site_id = site_id
        self.data_url = data_url
        self.solar_key = solar_key
        self.lon = lon
        self.lat = lat
        self.height = height

    def download_current_solar_data(self):
        """
        Downloads current solar station summary information
        :return: current station information in json format
        :except: throws excetion when response status hasn't been 200
        """
        url = '%s/site/%s/overview?api_key=%s' % (self.data_url, self.site_id, self.solar_key)
        return self.get(url)

    def update(self):
        """
        This method updates current data of the configured solar power
        TODO: This method is not UNIT TESTED!
        """
        self.logger.info('SolarData.py updating')

        solar_data = self.download_current_solar_data()

        power = solar_data['overview']['currentPower']['power']
        solar_datetime_str = solar_data['overview']['lastUpdateTime']

        session = self.create_session()

        solar_data_db = SolarData(solar_datetime_str, power)

        # calculate solar position on this datetime
        (azimuth, height) = sun.calculate_sun(
            datetime.strptime(solar_datetime_str, '%Y-%m-%d %H:%M:%S'), self.lon, self.lat, self.height)
        sun_data_db = SunData(solar_datetime_str, azimuth, height)

        session.add(solar_data_db)
        session.add(sun_data_db)

        session.commit()
        session.close_all()

        self.logger.debug('Updated: %r' % solar_data)

    def update_from_file(self, file_name):
        """
        Updates old data from a file.
        :param file_name:
        :return: 
        """
        self.logger.info('SolarData.py updating from file %s' % file_name)
        # TODO: it should combine data from a file with existing in database

    def update_datetime_period(self, date_period):
        """
        :param date_period: string date period from:to in format as follow: YYYYY-MM-DD:YYYY-MM-DD
        """
        dates = date_period.split(':')
        from_date = datetime.strptime(dates[0], "%Y-%m-%d")
        to_date = datetime.strptime(dates[1], "%Y-%m-%d")

        data = self.download_datetime_period(from_date, to_date)

        session = self.create_session()

        # propagate data to database
        for measure in data['energy']['values']:
            self.logger.debug('date: %s, measure: %s' % (measure['date'], measure['value']))
            entity = session.query(SolarData).filter_by(datetime=measure['date'])
            if entity is None:
                # create new object
                self.logger.debug('creating new solar_data entry')
                solar_data = SolarData(datetime=measure['date'], power=measure['value'])
                session.add(solar_data)
                session.commit()
            else:  # update existing data
                self.logger.debug('updating existing solar_data entry')
                entity.power = measure['value']
                session.commit()

        session.close()

    def download_datetime_period(self, from_date, to_date):
        """
        :param from_date: 
        :param to_date: 
        """
        url = '%s/site/%s/energy?timeUnit=QUARTER_OF_AN_HOUR' \
              '&startDate=%s&endDate=%s&api_key=%s' \
              % (self.data_url, self.site_id, from_date, to_date, self.solar_key)
        self.logger.debug(url)
        return self.get(url)

#    def update_daemonize(self):
#        """
#        This method is a wrapper for update method, it will periodically call update method as configured in
##        properties or command line parameters
#        TODO: This method is not UNIT TESTED!
#        """
#        self.logger.info('SolarData.py will update as a daemon')
#        self.update()
#
#        self.logger.debug('SolarData.py is going to sleep for %s seconds' % self.updater_interval)
#        time.sleep(int(self.updater_interval))
#        self.update_daemonize()


