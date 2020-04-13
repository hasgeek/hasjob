# -*- coding: utf-8 -*-
"""Board domains and locations

Revision ID: 3ac38e8fc78b
Revises: 275e9a964a9f
Create Date: 2014-11-19 12:39:02.691552

"""

# revision identifiers, used by Alembic.
revision = '3ac38e8fc78b'
down_revision = '275e9a964a9f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'board_domain',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.Unicode(length=80), nullable=False),
        sa.ForeignKeyConstraint(['board_id'], ['board.id']),
        sa.PrimaryKeyConstraint('board_id', 'domain'),
    )
    op.create_index('ix_board_domain_domain', 'board_domain', ['domain'])
    op.create_table(
        'board_location',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('geonameid', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['board_id'], ['board.id']),
        sa.PrimaryKeyConstraint('board_id', 'geonameid'),
    )
    op.create_index('ix_board_location_geonameid', 'board_location', ['geonameid'])
    op.create_index('ix_job_location_geonameid', 'job_location', ['geonameid'])


def downgrade():
    op.drop_index('ix_job_location_geonameid')
    op.drop_index('ix_board_location_geonameid')
    op.drop_table('board_location')
    op.drop_index('ix_board_domain_domain')
    op.drop_table('board_domain')
