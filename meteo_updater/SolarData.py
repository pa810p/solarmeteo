###
# SolarMeteo    : https://github.com/pa810p/solarmeteo
# Author        : Pawel Prokop
# License       : GNU GENERAL PUBLIC LICENSE v3
###



from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Float, DateTime, Integer, Sequence

Base = declarative_base()


class SolarData(Base):
    __tablename__ = 'solar_data'

    id = Column(Integer, Sequence('solar_data_id_seq'), primary_key=True)
    datetime = Column(DateTime, unique=True, nullable=False)
    power = Column(Float, nullable=False)

    def __init__(self, datetime, power):
        super().__init__()
        if datetime is None:
            raise Exception('no datetime')
        self.datetime = datetime

        if power is None:
            raise Exception('no power data')
        self.power = power

    def __repr__(self):
        return "<SolarData(id=%s, datetime=%s, power=%s)>" % (
            str(self.id) if not None else 'None', self.datetime, self.power)
