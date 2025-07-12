from sqlalchemy import Column, String, Float, Integer, Sequence
from sqlalchemy.orm import relationship

from .base import Base

class EsaStation(Base):
    __tablename__ = 'esa_station'

    id = Column(Integer, Sequence('esa_station_id_seq'), primary_key=True)
    name = Column(String, nullable=False)
    street = Column(String)
    post_code = Column(String)
    city = Column(String)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)

    station_data = relationship("EsaStationData", back_populates="station")


    def __init__(self, name, street=None, post_code=None, city=None, longitude=None, latitude=None):
        self.name = name
        self.street = street
        self.post_code = post_code
        self.city = city
        self.longitude = longitude
        self.latitude = latitude


    def __repr__(self):
        return f"<EsaStation(id={self.id}, name='{self.name}', city='{self.city}', longitude={self.longitude}, latitude={self.latitude})>"