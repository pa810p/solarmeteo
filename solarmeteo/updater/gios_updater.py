from logging import getLogger
import time
import random
from sqlite3 import IntegrityError

from sqlalchemy.exc import IntegrityError

from solarmeteo.model.gios_station import GiosStation
from solarmeteo.model.gios_station_data import GiosStationData, Parameter

logger = getLogger(__name__)

from solarmeteo.updater.updater import Updater

LIST_OF_STATIONS = "Lista stacji pomiarowych"

INDEX_DATE_BASE = "Data danych źródłowych, z których policzono wartość indeksu dla wskaźnika"
INDEX_VALUE_BASE = "Wartość indeksu dla wskaźnika"

INDEX_SO2 = "SO2"
INDEX_NO2 = "NO2"
INDEX_PM10 = "PM10"
INDEX_PM25 = "PM2.5"
INDEX_O3 = "O3"

INDEX_MAP = {
    INDEX_SO2: 'so2',
    INDEX_NO2: 'no2',
    INDEX_PM10: 'pm10',
    INDEX_PM25: 'pm25',
    INDEX_O3: 'o3'
}



class GiosUpdater(Updater):


    def __init__(self, meteo_db_url, gios_url, max_delay_sec=3):
        logger.info("Create Gios Updater")
        super(GiosUpdater, self).__init__(meteo_db_url, 0)
        self.gios_url = gios_url
        self.max_delay_sec = max_delay_sec


    def update_stations(self):
        logger.debug("Update stations")
        url = f"{self.gios_url}/station/findAll?page=0&size=300"
        stations_json = self.get(url)
        # for testing purpose
        # with open('data/gios_station_all.json', 'r', encoding='utf-8') as f:
        #     import json
        #     stations_json = json.load(f)

        logger.debug(f"Downloaded {len(stations_json[LIST_OF_STATIONS])} stations")

        session = self.create_session()
        for station_json in stations_json[LIST_OF_STATIONS]:
            logger.debug(f"Got station name: {station_json["Nazwa stacji"]}")

            station = GiosStation(
                gios_id=station_json["Identyfikator stacji"],
                station_code=station_json["Kod stacji"],
                station_name=station_json["Nazwa stacji"],
                latitude=float(station_json["WGS84 φ N"]),
                longitude=float(station_json["WGS84 λ E"]),
                city_id=station_json["Identyfikator miasta"],
                city_name=station_json["Nazwa miasta"],
                commune=station_json["Gmina"],
                district=station_json["Powiat"],
                voivodeship=station_json["Województwo"],
                street=station_json["Ulica"]
            )

            session.add(station)

        session.commit()
        session.close_all()

    def update_all_stations_data(self):
        logger.debug("Update all stations data")
        session = self.create_session()
        logger.debug("Session created")
        stations = session.query(GiosStation).all()
        random.shuffle(stations)
        try:
            for station in stations:
                url = f"{self.gios_url}/aqindex/getIndex/{station.gios_id}"
                station_data_json = self.get(url, timeout=5)
                for index, column in INDEX_MAP.items():
                    datetime = station_data_json["AqIndex"][f"{INDEX_DATE_BASE} {index}"]
                    value = station_data_json["AqIndex"][f"{INDEX_VALUE_BASE} {index}"]
                    if datetime is not None and value is not None:
                        param = session.query(Parameter).filter_by(name=column).first()
                        station_data = GiosStationData(
                            gios_station_id=station.id,
                            parameter_id=param.id if param else None,
                            datetime=datetime,
                            value=value
                        )
                        try:
                            session.add(station_data)
                            session.commit()
                            logger.debug(f"{station.gios_id} added {column}={value} on {datetime}")
                        except IntegrityError:
                            logger.warning(f"Constraint violation on {station.gios_id} added {column}={value} on {datetime}")
                    else:
                        logger.debug(f"{station.id} {index}=null ")
                # randomized dela between requests
                time.sleep(random.uniform(1, self.max_delay_sec))
        finally:
            session.close_all()
            logger.debug("Session closed")





