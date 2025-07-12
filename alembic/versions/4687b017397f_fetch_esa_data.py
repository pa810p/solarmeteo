"""fetch esa data

Revision ID: 4687b017397f
Revises: f68703c8244d
Create Date: 2025-07-10 09:54:35.790476

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy import Column, Integer, Sequence, String, Float, DateTime, ForeignKey, text

from sqlalchemy.sql.ddl import CreateSequence, DropSequence


# revision identifiers, used by Alembic.
revision = '4687b017397f'
down_revision = 'f68703c8244d'
branch_labels = None
depends_on = None


def upgrade():

    op.execute(CreateSequence(Sequence('esa_station_id_seq')))

    op.create_table(
        'esa_station',
        Column('id', Integer(), Sequence('esa_station_id_seq'), primary_key=True,
               server_default=text("nextval('esa_station_id_seq")),
        Column('name', String(), nullable=False),
        Column('street', String()),
        Column('post_code', String()),
        Column('city', String()),
        Column('longitude', Float(), nullable=False),
        Column('latitude', Float(), nullable=False))

    op.execute(CreateSequence(Sequence('esa_station_id_seq')))

    op.create_table(
        'esa_station_data',
        Column('id', Integer(), Sequence('esa_station_data_id_seq'), primary_key=True,
                  server_default=text("nextval('esa_station_data_id_seq'")),
        Column('esa_station_id', Integer(), ForeignKey('esa_station.id'), nullable=False),
        Column('humidity', Float(), nullable=False),
        Column('pressure', Float(), nullable=False),
        Column('temperature', Float(), nullable=False),
        Column('pm10', Float(), nullable=False),
        Column('pm25', Float(), nullable=False),
        Column('timestamp', DateTime(), nullable=False)
    )


def downgrade():
    op.drop_table('esa_station_data')
    op.execute(DropSequence(Sequence('esa_station_data_id_seq')))
    op.drop_table('esa_station')
    op.execute(DropSequence(Sequence('esa_station_id_seq')))