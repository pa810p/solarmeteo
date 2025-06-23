import base64
import zlib
from dataclasses import dataclass
from operator import and_
from collections import defaultdict

import numpy as np

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from model.frame import FrameType, Frame
from model.station import Station
from model.station_data import StationData


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


    def provide_stations_by_datetimes(self, column, datetimes):

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


    def provide_frames_by_type_and_datetimes(self, heatmap, target_datetimes):
        session = self.create_session()
        result = ((session.query(Frame.datetime, Frame.body, Frame.dtype, Frame.shape)
                .join(FrameType))
                .filter(
                FrameType.name == heatmap,
                        Frame.datetime.in_(target_datetimes)
            )).all()

        session.close()

        frames = {}
        for (datetime, body, dtype, shape) in result:
            frames [datetime] = np.frombuffer(
                    zlib.decompress(base64.b64decode(body)),
                    dtype=np.dtype(dtype)
                ).reshape(tuple(int(x) for x in shape.split(',')))


        return frames


    # def provide_frames(self, heatmap):
    #     latest_datetimes = self.get_last_datetimes(self.last)
    #     frames = self.get_frames_by_type_and_datetimes(heatmap, latest_datetimes)
    #     return frames


    def store_frames(self, heatmap, frames):
        session = self.create_session()

        frame_type = session.query(FrameType).filter_by(name=heatmap).first()
        if not frame_type:
            frame_type = FrameType(name=heatmap)
            session.add(frame_type)
            session.flush()  # Generate ID for new type

        for (datetime, frame) in frames:
            assert isinstance(frame, np.ndarray)
            new_frame = Frame(
                type_id=frame_type.id,
                datetime=datetime,
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


    def provide(self, column="temperature"):
        return super().provide(column)

    def provide_frames_by_type_and_datetimes(self, heatmap="temperature", datetimes = None):
        return super().provide_frames_by_type_and_datetimes(heatmap, datetimes)


class PressureProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1):
        super().__init__(meteo_db_url, last)


    def provide(self, column="pressure"):
        return super().provide(column)

    def provide_frames_by_type_and_datetimes(self, heatmap="pressure", datetimes = None):
        return super().provide_frames_by_type_and_datetimes(heatmap, datetimes)


class HumidityProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1):
        super().__init__(meteo_db_url, last)

    def provide(self, column="humidity"):
        return super().provide(column)

    def provide_frames_by_type_and_datetimes(self, heatmap="humidity", datetimes = None):
        return super().provide_frames_by_type_and_datetimes(heatmap, datetimes)


class  PrecipitationProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1):
        super().__init__(meteo_db_url, last)

    def provide(self, column="precipitation"):
        return super().provide(column)

    def provide_frames_by_type_and_datetimes(self, heatmap="precipitation", datetimes = None):
        return super().provide_frames_by_type_and_datetimes(heatmap, datetimes)


class WindProvider(DataProvider):

    def __init__(self, meteo_db_url, last=1):
        super().__init__(meteo_db_url, last)

    def provide(self, column="wind_speed"):
        return super().provide(column)

    def provide_frames_by_type_and_datetimes(self, heatmap="wind", datetimes = None):
        return super().provide_frames_by_type_and_datetimes(heatmap, datetimes)

