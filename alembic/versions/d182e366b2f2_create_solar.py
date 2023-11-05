"""create solar

Revision ID: d182e366b2f2
Revises: 3709f40cf7e6
Create Date: 2019-10-31 21:26:53.731421

"""

from alembic import op

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, Integer, Sequence
from sqlalchemy.sql.ddl import CreateSequence, DropSequence

revision = 'd182e366b2f2'
down_revision = '3709f40cf7e6'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(CreateSequence(Sequence('solar_data_id_seq')))
    op.create_table('solar_data',
                    Column('id', Integer, Sequence('solar_data_id_seq'), primary_key=True,
                          server_default=sa.text("nextval('solar_data_id_seq'::regclass)")),
                    Column('datetime', DateTime, unique=True, nullable=False, primary_key=True),
                    Column('power', Integer)
                    )


def downgrade():
    op.drop_table('solar_data')
    op.execute(DropSequence(Sequence('solar_data_id_seq')))

