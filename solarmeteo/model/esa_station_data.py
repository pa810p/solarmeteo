from sqlalchemy import Column, Float, DateTime, Integer, ForeignKey, Sequence
from sqlalchemy.orm import relationship

from .base import Base

class EsaStationData(Base):
    __tablename__ = 'esa_station_data'

    id = Column(Integer, Sequence('esa_station_data_id_seq'), primary_key=True)
    esa_station_id = Column(Integer, ForeignKey('esa_station.id'), nullable=False)
    humidity = Column(Float, nullable=False)
    pressure = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    pm10 = Column(Float, nullable=False)
    pm25 = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    station = relationship("EsaStation", back_populates="station_data")


    def __init__(self, esa_station_id, humidity, pressure, temperature, pm10, pm25, datetime):
        self.esa_station_id = esa_station_id
        self.humidity = humidity
        self.pressure = pressure
        self.temperature = temperature
        self.pm10 = pm10
        self.pm25 = pm25
        self.datetime = datetime


    def __repr__(self):
        return (
            f"<EsaStationData(id={self.id}, esa_station_id={self.esa_station_id}, "
            f"humidity={self.humidity}, pressure={self.pressure}, "
            f"temperature={self.temperature}, pm10={self.pm10}, "
            f"pm25={self.pm25}, datetime={self.datetime})>"
        )


