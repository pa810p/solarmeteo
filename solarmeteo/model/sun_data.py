from sqlalchemy import Column, Integer, DateTime, Sequence, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SunData(Base):
    __tablename__ = 'sun_data'

    id = Column(Integer, Sequence('sun_data_id_seq'), primary_key=True)
    datetime = Column(DateTime, unique=True, nullable=False)
    azimuth = Column(Float, nullable=False)
    height = Column(Float, nullable=False)

    def __init__(self, datetime, azimuth, height):
        super().__init__()
        self.datetime = datetime
        self.azimuth = azimuth
        self.height = height

    def __repr__(self):
        return '<SunData(id=%s, datetime=%s, azimuth=%s, height=%s' % (
            self.id, str(self.datetime), self.azimuth, self.height
        )
