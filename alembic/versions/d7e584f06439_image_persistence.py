"""image persistence

Revision ID: d7e584f06439
Revises: f82c33931b10
Create Date: 2025-06-16 21:24:05.007225

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7e584f06439'
down_revision = 'f82c33931b10'
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        'frame_types',
        sa.Column('id', sa.Integer, sa.Sequence('frame_types_id_seq'), primary_key=True),
        sa.Column('name', sa.String, unique=True, nullable=False)
    )

    op.create_table(
        'frames',
        sa.Column('id', sa.Integer, sa.Sequence('frames_id_seq'), primary_key=True),
        sa.Column('type_id', sa.Integer, sa.ForeignKey('frame_types.id'), nullable=False),
        sa.Column('datetime', sa.DateTime, nullable=False),
        sa.Column('body', sa.String, nullable=False)
    )

def downgrade():
    op.drop_table('frames')
    op.drop_table('frame_types')
