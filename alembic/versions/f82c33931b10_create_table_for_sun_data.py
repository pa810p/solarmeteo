"""Create table for sun data

Revision ID: f82c33931b10
Revises: d182e366b2f2
Create Date: 2020-03-09 18:15:22.625229

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import Column, Integer, Sequence, Float, DateTime
from sqlalchemy.sql.ddl import CreateSequence, DropSequence

revision = 'f82c33931b10'
down_revision = 'd182e366b2f2'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(CreateSequence(Sequence('sun_data_id_seq')))
    # op.create_index('ix_sun_data_id', 'sun_data', ['sun_data_id'], unique=True)
    op.create_table('sun_data',
                    Column('id', Integer, Sequence('sun_data_id_seq'), primary_key=True,
                           server_default=sa.text("nextval('sun_data_id_seq'::regclass)")),
                    Column('datetime', DateTime, nullable=False),
                    Column('azimuth', Float, nullable=False),
                    Column('height', Float, nullable=False)
                    )


def downgrade():
    op.drop_table('sun_data')
    op.execute(DropSequence(Sequence('sun_data_id_seq')))

