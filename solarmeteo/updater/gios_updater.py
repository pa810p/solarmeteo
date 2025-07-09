from logging import getLogger

from solarmeteo.model.gios_station import GiosStation

logger = getLogger(__name__)

from solarmeteo.updater.updater import Updater

LIST_OF_STATIONS = "Lista stacji pomiarowych"

INDEX_DATE_BASE = "Data danych źródłowych, z których policzono wartość indeksu dla wskaźnika"


class GiosUpdater(Updater):


    def __init__(self, meteo_db_url, gios_url):
        logger.info("Create Gios Updater")
        super(GiosUpdater, self).__init__(meteo_db_url, 0)
        self.gios_url = gios_url


    def update_stations(self):
        logger.debug("Update stations")
        url = f"{self.gios_url}/station/findAll?page=0&size=300"
        stations_json = self.get(url)
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


    def update_stations_data(self):
        pass


