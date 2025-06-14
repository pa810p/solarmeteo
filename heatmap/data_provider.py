from dataclasses import dataclass
from operator import and_
from collections import defaultdict

import numpy as np

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from meteo_updater.Station import Station
from meteo_updater.StationData import StationData


@dataclass
class StationValue:
    lon: np.float64
    lat: np.float64
    value: np.float64
    name: str


class DataProvider:


    def __init__(self, meteo_db_url, last=1, from_time=None, until_time=None):
        self.meteo_db_url = meteo_db_url
        self.last = last
        self.from_time = from_time
        self.until_time = until_time


    def create_connection(self):
        """
        Creates connection to database
        """
        engine = create_engine(self.meteo_db_url)
        return engine.connect()

    def create_session(self):
        """
        Creates a database session
        """
        session = sessionmaker(bind=self.create_connection())
        return session()



class TemperatureProvider(DataProvider):


    def __init__(self, meteo_db_url, last=1, from_time=None, until_time=None):
        super().__init__(meteo_db_url, last, from_time, until_time)


    def provide(self):
        session = self.create_session()

        latest_datetimes = session.execute(
            select(StationData.datetime)
            .distinct()  # Ensure uniqueness
            .order_by(StationData.datetime.desc())  # Newest first
            .limit(self.last)
        ).scalars().all()

        # Fetch all stations for these datetimes
        results = session.execute(
            select(
                StationData.datetime,
                Station.longitude,
                Station.latitude,
                StationData.temperature,
                Station.name
            )
            .join(Station, Station.id == StationData.station_id)
            .where(
                and_(
                    StationData.datetime.in_(latest_datetimes),  # Filter by top N datetimes
                    StationData.temperature.isnot(None)
                )
            )
            .order_by(StationData.datetime.desc())  # Sort by datetime (newest first)
        ).all()

        session.close()

        # Group stations by datetime (using defaultdict)
        datetime_to_stations = defaultdict(list)
        for datetime, lon, lat, temp, name in results:
            datetime_to_stations[datetime].append(
                StationValue(np.float64(lon), np.float64(lat), np.float64(temp), name)
            )

        # Convert to a sorted list of tuples [(datetime, stations), ...]
        sorted_map = sorted(
            datetime_to_stations.items(),
            key=lambda x: x[0],  # Sort by datetime
            reverse=True         # Newest first
        )

        return sorted_map
