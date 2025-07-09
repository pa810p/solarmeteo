from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Boolean, String, Integer, Sequence, DateTime
from sqlalchemy.orm import relationship

Base = declarative_base()

class Parameter(Base):

    __tablename__ = 'gios_parameter'

    id = Column(Integer, Sequence('gios_parameter_id_seq'), primary_key=True)
    name = Column(String, nullable=False)

    station_data = relationship('GiosStationData', back_populates='parameter')


class GiosStationData(Base):

    __tablename__ = 'gios_station_data'

    id = Column(Integer, Sequence('gios_station_data_id_seq'), primary_key=True)
    gios_station_id = Column(Integer, nullable=False)
    datetime = Column(DateTime, nullable=False)
    parameter_id = Column(Integer, nullable=False)
    value = Column(Integer, nullable=False)
    critical = Column(Boolean, default=False)

    parameter = relationship("Parameter", back_populates="station_data")

    so2 = Column(Integer),
    no2 = Column(Integer),
    pm10 = Column(Integer),
    pm25 = Column(Integer),
    o3 = Column(Integer),

    gios_station = relationship("GiosStation", back_populates="station_data")

    def __repr__(self):
        return f"<GiosStationData(id={self.id}, gios_station_id={self.gios_station_id}, datetime={self.datetime}, measurement_id{self.measurement_id})>"

