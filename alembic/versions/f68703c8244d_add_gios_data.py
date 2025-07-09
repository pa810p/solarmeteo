"""add gios data

Revision ID: f68703c8244d
Revises: d7e584f06439
Create Date: 2025-07-08 19:59:41.170592

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy import Column, Integer, Sequence, Float, String, DateTime, Boolean, MetaData, Table
from sqlalchemy.sql.ddl import CreateSequence, DropSequence

# revision identifiers, used by Alembic.
revision = 'f68703c8244d'
down_revision = 'd7e584f06439'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(CreateSequence(Sequence('gios_station_id_seq')))
    Column('id', Integer, Sequence('gios_station_id_seq'), primary_key=True,
       server_default=sa.text("nextval('gios_station_id_seq'::regclass)")),

    op.create_table(
        'gios_station',
        Column('id', Integer, Sequence('gios_station_id_seq'), primary_key=True,
               server_default=sa.text("nextval('gios_station_id_seq')")),
        Column('station_name', String, nullable=False, unique=True),
        Column('gios_id', Integer, nullable=False, index=True, unique=True),
        Column('longitude', Float),
        Column('latitude', Float),
        Column('voivodeship', String),
        Column('district', String),
        Column('commune', String),
        Column('city_id', Integer),
        Column('city_name', String),
        Column('street', String),
        Column('station_code', String)
    )

    op.execute(CreateSequence(Sequence('gios_parameter_id_seq')))
    op.create_table(
        'gios_parameter',
        Column('id', Integer, Sequence('gios_parameter_id_seq'), primary_key=True,
               server_default=sa.text("nextval('gios_parameter_id_seq')")),
        Column('name', String, nullable=False, unique=True)),


    gios_parameter_table = Table(
        'gios_parameter',
        MetaData(),
        Column('id', Integer, primary_key=True),
        Column('name', String, unique=True, nullable=False)

    )

    op.bulk_insert(
        gios_parameter_table,
        [
            {'name': 'so2'},
            {'name': 'no2'},
            {'name': 'pm10'},
            {'name': 'pm25'},
            {'name': 'o3'}
        ]
    )

    op.execute(CreateSequence(Sequence('gios_station_data_id_seq')))
    op.create_table(
        'gios_station_data',
        Column('id', Integer, Sequence('gios_station_data_id_seq'), primary_key=True,
               server_default=sa.text("nextval('gios_station_data_id_seq')")),
        Column('gios_station_id', Integer, sa.ForeignKey('gios_station.id'), nullable=False),
        Column('parameter_id', Integer, sa.ForeignKey('gios_parameter.id'), nullable=False),
        Column('datetime', DateTime, nullable=False),
        Column('value', Integer),
    )
    op.create_index('ix_gios_station_data_station_parameter_datetime', 'gios_station_data',
                    ['gios_station_id', 'parameter_id', 'datetime'], unique=True)


def downgrade():
    op.drop_index('ix_gios_station_data_station_parameter_datetime')
    op.drop_index('ix_gios_station_gios_id')
    op.drop_table('gios_station_data')
    op.execute(DropSequence(Sequence('gios_station_data_id_seq')))
    op.drop_table('gios_parameter')
    op.execute(DropSequence(Sequence('gios_parameter_id_seq')))
    op.drop_table('gios_station')
    op.execute(DropSequence(Sequence('gios_station_id_seq')))

