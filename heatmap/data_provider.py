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

    def provide(self, column):
        session = self.create_session()

        latest_datetimes = session.execute(
            select(StationData.datetime)
            .distinct()
            .order_by(StationData.datetime.desc())
            .limit(self.last)
        ).scalars().all()

        # Dynamically get the column from StationData
        data_column = getattr(StationData, column)

        results = session.execute(
            select(
                StationData.datetime,
                Station.longitude,
                Station.latitude,
                data_column,
                Station.name
            )
            .join(Station, Station.id == StationData.station_id)
            .where(
                and_(
                    StationData.datetime.in_(latest_datetimes),
                    data_column.isnot(None)
                )
            )
            .order_by(StationData.datetime.desc())
        ).all()

        session.close()

        datetime_to_stations = defaultdict(list)
        for datetime, lon, lat, value, name in results:
            datetime_to_stations[datetime].append(
                StationValue(np.float64(lon), np.float64(lat), np.float64(value), name)
            )

        sorted_map = sorted(
            datetime_to_stations.items(),
            key=lambda x: x[0],
            reverse=True
        )

        return sorted_map



class TemperatureProvider(DataProvider):


    def __init__(self, meteo_db_url, last=1, from_time=None, until_time=None):
        super().__init__(meteo_db_url, last, from_time, until_time)


    def provide(self, column="temperature"):
        return super().provide(column)


class PressureProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1, from_time=None, until_time=None):
        super().__init__(meteo_db_url, last, from_time, until_time)


    def provide(self, column="pressure"):
        return super().provide(column)


class HumidityProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1, from_time=None, until_time=None):
        super().__init__(meteo_db_url, last, from_time, until_time)


    def provide(self, column="humidity"):
        return super().provide(column)


class  PrecipitationProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1, from_time=None, until_time=None):
        super().__init__(meteo_db_url, last, from_time, until_time)


    def provide(self, column="precipitation"):
        return super().provide(column)


class WindProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1, from_time=None, until_time=None):
        super().__init__(meteo_db_url, last, from_time, until_time)

    def provide(self, column="wind_speed"):
        return super().provide(column)