"""image persistence

Revision ID: d7e584f06439
Revises: f82c33931b10
Create Date: 2025-06-16 21:24:05.007225

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy import Column, Integer, Sequence, String, DateTime, ForeignKey, Table, MetaData

from sqlalchemy.sql.ddl import CreateSequence, DropSequence

# revision identifiers, used by Alembic.
revision = 'd7e584f06439'
down_revision = 'f82c33931b10'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(CreateSequence(Sequence('frame_types_id_seq')))
    op.create_table(
        'frame_types',
        Column('id', Integer, Sequence('frame_types_id_seq'), primary_key=True,
               server_default=sa.text("nextval('frame_types_id_seq')")),
                Column('name', String, unique=True, nullable=False)
    )
    frame_types_table = Table(
        'frame_types',
        MetaData(),
        Column('id', Integer, primary_key=True),
        Column('name', String, unique=True, nullable=False)
    )

    op.bulk_insert(
        frame_types_table,
        [
                {'name': 'temperature'},
                {'name': 'pressure'},
                {'name': 'precipitation'},
                {'name': 'humidity'},
                {'name': 'wind'}
            ]
    )

    op.execute(CreateSequence(Sequence('frames_id_seq')))
    op.create_table(
        'frames',
        Column('id', Integer, Sequence('frames_id_seq'), primary_key=True,
               server_default=sa.text("nextval('frames_id_seq')")),
        Column('type_id', Integer, ForeignKey('frame_types.id'), nullable=False),
        Column('datetime', DateTime, nullable=False),
        Column('body', String, nullable=False),
        Column('dtype', String(20)),
        Column('shape', String(50))
    )

def downgrade():
    op.drop_table('frames')
    op.execute(DropSequence(Sequence('frames_id_seq')))
    op.drop_table('frame_types')
    op.execute(DropSequence(Sequence('frame_types_id_seq')))