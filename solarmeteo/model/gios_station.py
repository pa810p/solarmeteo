from sqlalchemy import Column, Float, String, Integer, Sequence
from sqlalchemy.orm import relationship
from .base import Base

class GiosStation(Base):
    __tablename__ = 'gios_station'

    id = Column(Integer, Sequence('gios_station_id_seq'), primary_key=True)
    station_name = Column(String, nullable=False)
    gios_id = Column(Integer, nullable=False, index=True, unique=True)
    longitude = Column(Float)
    latitude = Column(Float)
    voivodeship = Column(String)
    district = Column(String)
    commune = Column(String)
    city_id = Column(Integer)
    city_name = Column(String)
    street = Column(String)
    station_code = Column(String)

    # Use consistent naming (station_data instead of gios_station_data)
    station_data = relationship("GiosStationData", back_populates="station")

    def __init__(self, station_name, gios_id, longitude=None, latitude=None, voivodeship=None,
                 district=None, commune=None, city_id=None, city_name=None, street=None, station_code=None):
        self.station_name = station_name
        self.gios_id = gios_id
        self.longitude = longitude
        self.latitude = latitude
        self.voivodeship = voivodeship
        self.district = district
        self.commune = commune
        self.city_id = city_id
        self.city_name = city_name
        self.street = street
        self.station_code = station_code


    def __repr__(self):
        return f"<GiosStation(id={self.id}, station_name={self.station_name!r}, gios_id={self.gios_id})>"


