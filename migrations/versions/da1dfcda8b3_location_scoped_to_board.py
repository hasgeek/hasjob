"""Location scoped to board

Revision ID: da1dfcda8b3
Revises: d19802512a1
Create Date: 2016-05-03 11:06:14.239742

"""

# revision identifiers, used by Alembic.
revision = 'da1dfcda8b3'
down_revision = 'd19802512a1'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column(
        'location',
        sa.Column(
            'board_id', sa.Integer(), nullable=False, server_default=sa.text('1')
        ),
    )
    op.alter_column('location', 'board_id', server_default=None)
    op.create_index(
        op.f('ix_location_board_id'), 'location', ['board_id'], unique=False
    )
    op.drop_constraint('location_name_key', 'location', type_='unique')
    op.create_unique_constraint(
        'location_board_id_name_key', 'location', ['board_id', 'name']
    )
    op.create_foreign_key(
        'location_board_id_fkey', 'location', 'board', ['board_id'], ['id']
    )
    op.drop_constraint('location_pkey', 'location', type_='primary')
    op.create_primary_key('location_pkey', 'location', ['id', 'board_id'])


def downgrade():
    op.drop_constraint('location_pkey', 'location', type_='primary')
    op.create_primary_key('location_pkey', 'location', ['id'])
    op.drop_constraint('location_board_id_fkey', 'location', type_='foreignkey')
    op.drop_constraint('location_board_id_name_key', 'location', type_='unique')
    op.create_unique_constraint('location_name_key', 'location', ['name'])
    op.drop_index(op.f('ix_location_board_id'), table_name='location')
    op.drop_column('location', 'board_id')
