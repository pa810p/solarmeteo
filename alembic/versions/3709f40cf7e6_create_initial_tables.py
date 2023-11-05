"""create initial tables

Revision ID: 3709f40cf7e6
Revises: 
Create Date: 2019-10-03 15:11:21.181405

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import Column, Integer, Sequence, String, Float, DateTime, ForeignKey
from sqlalchemy.sql.ddl import CreateSequence, DropSequence

revision = '3709f40cf7e6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(CreateSequence(Sequence('station_id_seq')))
    op.create_table('station',
                    Column('id', Integer, Sequence('station_id_seq'), primary_key=True,
                           server_default=sa.text("nextval('station_id_seq'::regclass)")),
                    Column('name', String, nullable=False),
                    Column('imgw_id', Integer, nullable=False),
                    Column('longitude', Float),
                    Column('latitude', Float)
                    )
    op.execute(CreateSequence(Sequence('station_data_id_seq')))
    op.create_index('ix_station_imgw_id', 'station', ['imgw_id'], unique=True)
    op.create_table('station_data',
                    Column('id', Integer, Sequence('station_data_id_seq'), primary_key=True,
                           server_default=sa.text("nextval('station_data_id_seq'::regclass)")),
                    Column('station_id', Integer, ForeignKey('station.id', ondelete='CASCADE'), nullable=False),
                    Column('datetime', DateTime, nullable=False),
                    Column('temperature', Float),
                    Column('wind_speed', Integer),
                    Column('wind_direction', Integer),
                    Column('humidity', Float),
                    Column('precipitation', Float),
                    Column('pressure', Float)
                    )
    op.create_unique_constraint('uq_station_id_datetime', 'station_data', ['station_id', 'datetime'])


def downgrade():
    op.drop_table('station_data')
    op.execute(DropSequence(Sequence('station_data_id_seq')))
    op.drop_index('ix_station_imgw_id')
    op.drop_table('station')
    op.execute(DropSequence(Sequence('station_id_seq')))
