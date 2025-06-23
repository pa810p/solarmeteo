from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Frame(Base):
    __tablename__ = 'frames'

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey('frame_types.id'), nullable=False)
    datetime = Column(DateTime, nullable=False)
    body = Column(String, nullable=False)  # compresed base64-encoded string
    dtype = Column(String(20)) # needed to fully restore ndarray
    shape = Column(String(50)) # needed to fully restore ndarray

    type = relationship('FrameType', back_populates='frames')

class FrameType(Base):
    __tablename__ = 'frame_types'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    frames = relationship('Frame', back_populates='type')


