import base64
import zlib
from dataclasses import dataclass
from operator import and_
from collections import defaultdict

from logging import getLogger

import numpy as np

from sqlalchemy import create_engine, select, func, delete
from sqlalchemy.orm import sessionmaker

from solarmeteo.model import EsaStationData, EsaStation
from solarmeteo.model.frame import FrameType, Frame
from solarmeteo.model.station import Station
from solarmeteo.model.station_data import StationData

logger = getLogger("solarmeteo")

@dataclass
class StationValue:
    lon: np.float64
    lat: np.float64
    value: np.float64
    name: str

@dataclass
class StationWindValue(StationValue):
    direction: np.int16


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


    def get_last_datetimes(self, last):
        session = self.create_session()

        latest_datetimes = session.execute(
            select(StationData.datetime)
            .distinct()
            .order_by(StationData.datetime.desc())
            .limit(last)
        ).scalars().all()

        session.close()
        return latest_datetimes


    def delete_older_than_datetimes(self, heatmap, keep_datetimes):
        session = self.create_session()
        try:
            frame_type_id = session.execute(
                select(FrameType.id)
                .where(FrameType.name == heatmap)
            ).scalar_one()

            query = (
                delete(Frame)
                .where(Frame.datetime.not_in(keep_datetimes) &
                       (Frame.type_id == frame_type_id))
            )

            result = session.execute(query)
            session.commit()
            return result.rowcount
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


    def _delete_all_frames(self, heatmap):
        logger.info("Delete all frames.")
        session = self.create_session()
        frame_type_id = session.execute(
            select(FrameType.id)
            .where(FrameType.name == heatmap)
        ).scalar_one()

        query = (delete(Frame)
            .where(Frame.type_id == frame_type_id)
        )

        result = session.execute(query)
        session.commit()
        return result.rowcount


    def delete_older_frames(self, heatmap, keep_frames):
        if keep_frames == 0:
            self._delete_all_frames(heatmap)
        elif keep_frames > 0:
            logger.debug(f"Keeping last {keep_frames} of {heatmap} frames")
            datetimes = self.get_last_datetimes(keep_frames)
            if len(datetimes) > 0:
                return self.delete_older_than_datetimes(heatmap, datetimes)
        else:
            logger.debug("Keeping all frames.")
            return -1


    def provide_stations_by_datetimes(self, column : str, datetimes : list) -> list:
        """
        Provides station data for the specified column and datetimes.

        Args:
            column (str): The name of the data column to retrieve from StationData.
            datetimes (list): List of datetime objects to filter the data.

        Returns:
            list: Sorted list of tuples (datetime, [StationValue, ...]) in descending datetime order.
        """

        session = self.create_session()

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
                    StationData.datetime.in_(datetimes),
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


    def provide(self, column):
        latest_datetimes = self.get_last_datetimes(self.last)
        return self.provide_stations_by_datetimes(column, latest_datetimes)


    def provide_frames_by_type_and_datetimes(self, heatmap : str, datetimes : list ) -> dict:
        """
        Retrieves frames of a specific type (heatmap) for the given datetimes.

        Args:
            heatmap (str): The name of the heatmap or frame type to retrieve.
            datetimes (list): List of datetime objects to filter the frames.

        Returns:
            dict: A dictionary mapping datetime to the corresponding numpy array frame
        """
        if datetimes is None or len(datetimes) < 1:
            logger.error('Datetimes should be an array of at least one element. No frames will be provided')
            return None

        session = self.create_session()
        result = ((session.query(Frame.datetime, Frame.body, Frame.dtype, Frame.shape)
                   .join(FrameType))
        .filter(
            FrameType.name == heatmap,
            Frame.datetime.in_(datetimes)
        )).all()

        session.close()

        frames = dict()
        for (datetime, body, dtype, shape) in result:
            frames [datetime] = np.frombuffer(
                zlib.decompress(base64.b64decode(body)),
                dtype=np.dtype(dtype)
            ).reshape(tuple(int(x) for x in shape.split(',')))

        logger.debug(f"Providing stored frames for: {frames.keys()}")
        return frames


    # def provide_frames(self, heatmap):
    #     latest_datetimes = self.get_last_datetimes(self.last)
    #     frames = self.get_frames_by_type_and_datetimes(heatmap, latest_datetimes)
    #     return frames


    def store_frames(self, heatmap : str, frames : dict):
        """
        Stores frames of a specific heatmap type in the database.

        Args:
            heatmap (str): The name of the heatmap or frame type.
            frames (iterable): An iterable of (datetime, np.ndarray) tuples to store.

        Each frame is compressed, encoded, and stored with its metadata.
        """
        logger.debug("Store frames on database")
        session = self.create_session()

        frame_type = session.query(FrameType).filter_by(name=heatmap).first()
        if not frame_type:
            logger.info(f"Create new frametype: {heatmap}")
            frame_type = FrameType(name=heatmap)
            session.add(frame_type)
            session.flush()  # Generate ID for new type

        for key in frames:
            frame = frames[key]
            assert isinstance(frame, np.ndarray)
            new_frame = Frame(
                type_id=frame_type.id,
                datetime=key,
                body=base64.b64encode(zlib.compress(frame.tobytes())).decode('utf-8'),
                dtype=str(frame.dtype),
                shape=','.join(map(str, frame.shape))
            )
            session.add(new_frame)

        session.commit()
        session.close()


class TemperatureProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1):
        super().__init__(meteo_db_url, last)


    def provide_stations_by_datetimes(self, datetimes=None):
        return super().provide_stations_by_datetimes(column="temperature", datetimes=datetimes)

    def provide_frames_by_type_and_datetimes(self, datetimes = None):
        return super().provide_frames_by_type_and_datetimes("temperature", datetimes)


class PressureProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1):
        super().__init__(meteo_db_url, last)


    def provide_stations_by_datetimes(self, datetimes=None):
        return super().provide_stations_by_datetimes(column="pressure", datetimes=datetimes)

    def provide_frames_by_type_and_datetimes(self, datetimes = None):
        return super().provide_frames_by_type_and_datetimes("pressure", datetimes)


class HumidityProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1):
        super().__init__(meteo_db_url, last)

    def provide_stations_by_datetimes(self, datetimes=None):
        return super().provide_stations_by_datetimes(column="humidity", datetimes=datetimes)

    def provide_frames_by_type_and_datetimes(self, datetimes = None):
        return super().provide_frames_by_type_and_datetimes("humidity", datetimes)


class  PrecipitationProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1):
        super().__init__(meteo_db_url, last)

    def provide_stations_by_datetimes(self, datetimes=None):
        return super().provide_stations_by_datetimes(column="precipitation", datetimes=datetimes)

    def provide_frames_by_type_and_datetimes(self, datetimes = None):
        return super().provide_frames_by_type_and_datetimes("precipitation", datetimes)


class WindProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1):
        super().__init__(meteo_db_url, last)

    def provide(self, column="wind_speed"):
        return super().provide(column)

    def provide_stations_by_datetimes(self, datetimes = None):
        session = self.create_session()

        results = session.execute(
            select(
                StationData.datetime,
                Station.longitude,
                Station.latitude,
                StationData.wind_speed,
                StationData.wind_direction,
                Station.name
            )
            .join(Station, Station.id == StationData.station_id)
            .where(
                and_(
                    and_(
                        StationData.datetime.in_(datetimes),
                        StationData.wind_speed.isnot(None)
                    ),
                    StationData.wind_direction.isnot(None)
                )
                )
            .order_by(StationData.datetime.desc())
        ).all()

        session.close()

        datetime_to_stations = defaultdict(list)
        for datetime, lon, lat, value, direction, name in results:
            datetime_to_stations[datetime].append(
                StationWindValue(np.float64(lon), np.float64(lat), np.float64(value), name, np.int16(direction))
            )

        sorted_map = sorted(
            datetime_to_stations.items(),
            key=lambda x: x[0],
            reverse=True
        )

        return sorted_map

        # return super().provide_stations_by_datetimes(column="wind_speed", datetimes=datetimes)

    def provide_frames_by_type_and_datetimes(self, datetimes = None):
        return super().provide_frames_by_type_and_datetimes(heatmap = "wind", datetimes=datetimes)


class ESAProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1):
        super().__init__(meteo_db_url, last)

    def get_last_datetimes(self, last):
        session = self.create_session()

        latest_datetimes = session.execute(
            select(EsaStationData.datetime)
            .distinct()
            .order_by(EsaStationData.datetime.desc())
            .limit(last)
        ).scalars().all()

        session.close()

        return latest_datetimes

    def provide_stations_by_datetimes(self, column, datetimes):
        session = self.create_session()

        data_column = getattr(EsaStationData, column)

        query = (
            select(
                EsaStationData.datetime,
                func.avg(EsaStation.longitude).label("avg_longitude"),
                func.avg(EsaStation.latitude).label("avg_latitude"),
                func.avg(data_column).label("value"),
                EsaStation.city
            )
            .join(EsaStationData.station)  # Join the tables via relationship
            .where(EsaStationData.datetime.in_(datetimes))
            .group_by(EsaStation.city, EsaStationData.datetime)  # Group by city and datetime
            .order_by(EsaStation.city, EsaStationData.datetime)
        )

        results = session.execute(query).all()

        session.close_all()

        datetime_to_stations = defaultdict(list)
        for datetime, avg_longitude, avg_latitude, value, city in results:
            datetime_to_stations[datetime].append(
                StationValue(np.float64(avg_longitude), np.float64(avg_latitude), np.float64(value), city)
            )

        sorted_map = sorted(
            datetime_to_stations.items(),
            key=lambda x: x[0],
            reverse=True
        )

        return sorted_map

class PM10Provider(ESAProvider):

    def __init__(self, meteo_db_url, last=1):
        super().__init__(meteo_db_url, last)

    def provide_stations_by_datetimes(self, datetimes=None):
        return super().provide_stations_by_datetimes(column="pm10", datetimes=datetimes)

    def provide_frames_by_type_and_datetimes(self, datetimes = None):
        return super().provide_frames_by_type_and_datetimes("pm10", datetimes)


class PM25Provider(ESAProvider):

    def __init__(self, meteo_db_url, last=1):
        super().__init__(meteo_db_url, last)

    def provide_stations_by_datetimes(self, datetimes=None):
        return super().provide_stations_by_datetimes(column="pm25", datetimes=datetimes)

    def provide_frames_by_type_and_datetimes(self, datetimes = None):
        return super().provide_frames_by_type_and_datetimes("pm25", datetimes)


