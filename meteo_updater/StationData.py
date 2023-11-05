###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, DateTime, Sequence, ForeignKey
import logs.logs

Base = declarative_base()

IMGW_DATE = 'data_pomiaru'
IMGW_HOUR = 'godzina_pomiaru'
IMGW_TEMPERATURE = 'temperatura'
IMGW_WIND_SPEED = 'predkosc_wiatru'
IMGW_WIND_DIRECTION = 'kierunek_wiatru'
IMGW_HUMIDITY = 'wilgotnosc_wzgledna'
IMGW_PRECIPITATION = 'suma_opadu'
IMGW_PRESSURE = 'cisnienie'


class StationData(Base):
    __tablename__ = 'station_data'

    id = Column(Integer, Sequence('station_id_seq'), primary_key=True)
    station_id = Column(Integer, nullable=False)
    datetime = Column(DateTime, nullable=False)
    temperature = Column(Float)
    wind_speed = Column(Integer)
    wind_direction = Column(Integer)
    humidity = Column(Float)
    precipitation = Column(Float)
    pressure = Column(Float)

    def __init__(self, station_id, datetime, temperature, wind_speed, wind_direction, humidity, precipitation,
                 pressure):

        if not station_id:
            raise Exception('no station_id')
        if not datetime:
            raise Exception('no datetime')

        self.station_id = station_id
        self.datetime = datetime
        self.temperature = temperature
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
        self.humidity = humidity
        self.precipitation = precipitation
        self.pressure = pressure

    def __repr__(self):
        return '<StationData(id=%s, station_id=%s, datetime=%s, temperature=%s, wind_speed=%s, wind_direction=%s, ' \
            'humidity=%s, precipitation=%s, pressure=%s' % (self.id, self.station_id, str(self.datetime),
                                                            self.temperature, self.wind_speed, self.wind_direction,
                                                            self.humidity, self.precipitation, self.pressure)

