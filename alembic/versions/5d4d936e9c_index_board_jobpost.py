"""Index board jobpost

Revision ID: 5d4d936e9c
Revises: 4bd08758f049
Create Date: 2015-03-18 20:43:19.264986

"""

# revision identifiers, used by Alembic.
revision = '5d4d936e9c'
down_revision = '4bd08758f049'

from alembic import op


def upgrade():
    op.create_index(op.f('ix_board_jobpost_jobpost_id'), 'board_jobpost', ['jobpost_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_board_jobpost_jobpost_id'), table_name='board_jobpost')
