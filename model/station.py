###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Sequence

Base = declarative_base()

IMGW_STATION_ID = 'id_stacji'
IMGW_STATION_NAME = 'stacja'


class Station(Base):
    __tablename__ = 'station'

    id = Column(Integer, Sequence('station_id_seq'), primary_key=True)
    name = Column(String, nullable=False)
    imgw_id = Column(Integer, nullable=False, index=True, unique=True)
    longitude = Column(Float)
    latitude = Column(Float)

    def __init__(self, name, imgw_id, lon=None, lat=None):
        super().__init__()
        if not name:
            raise Exception('no name')
        if not imgw_id:
            raise Exception('no IMGW id')

        self.name = name
        self.imgw_id = imgw_id
        self.longitude = lon
        self.latitude = lat

    def __repr__(self):
        return "<Station(id=%s, name=%s, imgw_id=%s, lon=%s, lat=%s)>" % (
            str(self.id) if not None else 'None', self.name, self.imgw_id,
            str(self.longitude) if not None else 'None', str(self.latitude) if not None else 'None')

