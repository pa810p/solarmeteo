from operator import truediv

import sqlalchemy

from solarmeteo.model import EsaStation, EsaStationData
from solarmeteo.updater.updater import Updater

from logging import getLogger



logger = getLogger(__name__)



class EsaUpdater(Updater):

    def __init__(self, meteo_db_url, esa_data_url):
        super(EsaUpdater, self).__init__(meteo_db_url, 1)
        self.esa_data_url = esa_data_url


    def _find_station_by_name(self, session, name):
        station = session.query(EsaStation).filter(EsaStation.name == name).first()
        return station


    def _save_station(self, session, school_data):
        # school_data = station_json.get("school")
        if not school_data:
            logger.error("No 'school' data")
            return None

        station = EsaStation(
            name=school_data.get("name"),
            street=school_data.get("street"),
            post_code=school_data.get("post_code"),
            city=school_data.get("city"),
            longitude=school_data.get("longitude"),
            latitude=school_data.get("latitude"),
        )

        session.add(station)
        session.commit()
        logger.info(f"Created: {station}")
        return station


    def _get_station(self, session, station_json):
        station = self._find_station_by_name(session, station_json["name"])
        if not station:
            station = self._save_station(session, station_json)
            
        return station


    def _is_valid(self, esa_station_data) -> bool:
        return True

    
    def update(self):
        esa_json = self.get(self.esa_data_url)

        session = self.create_session()

        for smog in esa_json["smog_data"]:

            station = self._get_station(session, smog["school"])
            data = smog.get("data", {})

            esa_station_data = EsaStationData(
                esa_station_id=station.id,
                humidity=data.get("humidity_avg"),
                pressure=data.get("pressure_avg"),
                temperature=data.get("temperature_avg"),
                pm10=data.get("pm10_avg"),
                pm25=data.get("pm25_avg"),
                datetime=smog["timestamp"]
                )

            if self._is_valid(esa_station_data):
                try:
                    session.add(esa_station_data)
                    session.commit()
                    logger.debug(f"Added new station data with id: {esa_station_data.id}")

                except sqlalchemy.exc.IntegrityError as exception:
                    session.rollback()
                    logger.warning(f"Constraint violation on {esa_station_data.esa_station_id}, Exception: {exception.orig}")
            else:
                logger.warning(f"Invalid EsaStationData object: {esa_station_data}")

        # finally:
        session.close_all()
        logger.debug("Session closed")

