# -*- coding: utf-8 -*-
"""Geotargeted column

Revision ID: 23546c6d07e2
Revises: 348bd4e2226b
Create Date: 2015-01-31 23:17:41.737755

"""

# revision identifiers, used by Alembic.
revision = '23546c6d07e2'
down_revision = '348bd4e2226b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'campaign',
        sa.Column('geotargeted', sa.Boolean(), nullable=False, server_default='0'),
    )
    op.alter_column('campaign', 'geotargeted', server_default=None)
    op.create_check_constraint(
        'campaign_start_at_end_at', 'campaign', 'end_at > start_at'
    )


def downgrade():
    op.drop_constraint('campaign_start_at_end_at', 'campaign')
    op.drop_column('campaign', 'geotargeted')
