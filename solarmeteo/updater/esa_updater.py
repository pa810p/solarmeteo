from solarmeteo.model import EsaStation, EsaStationData
from solarmeteo.model.station import Station, IMGW_STATION_ID, IMGW_STATION_NAME
from solarmeteo.updater.updater import Updater

from logging import getLogger



logger = getLogger(__name__)



class EsaUpdater(Updater):

    def __init__(self, meteo_db_url, esa_data_url):
        super(EsaUpdater, self).__init__(meteo_db_url, 1)
        self.esa_data_url = esa_data_url


    def _find_station_by_name(self, name):
        session = self.create_session()
        station = session.query(Station).filter(Station.name == name).first()
        session.close()
        return station


    def _save_station(self, station_json):
        school_data = station_json.get("school")
        if not school_data:
            logger.error("No 'school' key in station_json")
            return None

        station = EsaStation(
            name=school_data.get("name"),
            street=school_data.get("street"),
            post_code=school_data.get("post_code"),
            city=school_data.get("city"),
            longitude=school_data.get("longitude"),
            latitude=school_data.get("latitude"),
        )

        session = self.create_session()
        session.add(station)
        session.commit()
        session.close()
        logger.info(f"Created: {station}")
        return station


    def _get_station(self, station_json):
        station = self._find_station_by_name(station_json["name"])
        if not station:
            station = self._save_station(station_json)
            
        return station
    
    
    def update(self):
        esa_json = self.get(self.esa_data_url)
        
        for smog in esa_json["smog_data"]:
            station = self._get_station(smog["school"])
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







"""

esa_station = EsaStation(
     name="SZKOŁA PODSTAWOWA IM. MARIANA FALSKIEGO W KRASZEWICACH",
     street="UL. SZKOLNA",
     post_code="63-522",
     city="KRASZEWICE",
     longitude="18.22403",
     latitude="51.51563"
 )
"""