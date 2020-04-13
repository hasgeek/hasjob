# -*- coding: utf-8 -*-
"""Campaign last view datetime

Revision ID: 8a37fe07ef9d
Revises: a55bb6a85c83
Create Date: 2018-02-22 00:26:16.042019

"""

# revision identifiers, used by Alembic.
revision = '8a37fe07ef9d'
down_revision = 'a55bb6a85c83'

from alembic import op
from sqlalchemy.sql import column, table
import sqlalchemy as sa

campaign_view = table(
    'campaign_view',
    column('updated_at', sa.DateTime),
    column('last_viewed_at', sa.DateTime),
    column('datetime', sa.DateTime),
    column('reset_at', sa.DateTime),
)

campaign_anon_view = table(
    'campaign_anon_view',
    column('updated_at', sa.DateTime),
    column('last_viewed_at', sa.DateTime),
    column('datetime', sa.DateTime),
    column('reset_at', sa.DateTime),
)


def upgrade():
    op.add_column(
        'campaign_anon_view', sa.Column('last_viewed_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'campaign_anon_view', sa.Column('reset_at', sa.DateTime(), nullable=True)
    )
    op.execute(
        campaign_anon_view.update().values(
            {
                'last_viewed_at': campaign_anon_view.c.updated_at,
                'reset_at': campaign_anon_view.c.datetime,
            }
        )
    )
    op.alter_column('campaign_anon_view', 'last_viewed_at', nullable=False)
    op.alter_column('campaign_anon_view', 'reset_at', nullable=False)

    op.add_column(
        'campaign_view', sa.Column('last_viewed_at', sa.DateTime(), nullable=True)
    )
    op.add_column('campaign_view', sa.Column('reset_at', sa.DateTime(), nullable=True))
    op.execute(
        campaign_view.update().values(
            {
                'last_viewed_at': campaign_view.c.updated_at,
                'reset_at': campaign_view.c.datetime,
            }
        )
    )
    op.alter_column('campaign_view', 'last_viewed_at', nullable=False)
    op.alter_column('campaign_view', 'reset_at', nullable=False)


def downgrade():
    op.drop_column('campaign_view', 'last_viewed_at')
    op.drop_column('campaign_view', 'reset_at')
    op.drop_column('campaign_anon_view', 'last_viewed_at')
    op.drop_column('campaign_anon_view', 'reset_at')
