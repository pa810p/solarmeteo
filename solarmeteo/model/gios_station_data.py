from sqlalchemy import Column, String, Integer, Sequence, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Parameter(Base):
    __tablename__ = 'gios_parameter'

    id = Column(Integer, Sequence('gios_parameter_id_seq'), primary_key=True)
    name = Column(String, nullable=False)

    station_data = relationship('GiosStationData', back_populates='parameter')


class GiosStationData(Base):
    __tablename__ = 'gios_station_data'

    id = Column(Integer, Sequence('gios_station_data_id_seq'), primary_key=True)
    gios_station_id = Column(Integer, ForeignKey('gios_station.id'), nullable=False)
    datetime = Column(DateTime, nullable=False)
    parameter_id = Column(Integer, ForeignKey('gios_parameter.id'), nullable=False)
    value = Column(Integer, nullable=False)

    # Relationships with consistent naming
    parameter = relationship("Parameter", back_populates="station_data")
    station = relationship("GiosStation", back_populates="station_data")

    def __init__(self, gios_station_id, datetime, parameter_id, value):
        self.gios_station_id = gios_station_id
        self.datetime = datetime
        self.parameter_id = parameter_id
        self.value = value

    def __repr__(self):
        return f"<GiosStationData(id={self.id}, gios_station_id={self.gios_station_id}, datetime={self.datetime}, measurement_id{self.measurement_id})>"

