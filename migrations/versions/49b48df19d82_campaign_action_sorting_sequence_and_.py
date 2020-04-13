# -*- coding: utf-8 -*-
"""Campaign action sorting sequence and icon

Revision ID: 49b48df19d82
Revises: c20bd2c9b35
Create Date: 2015-01-28 18:24:13.549411

"""

# revision identifiers, used by Alembic.
revision = '49b48df19d82'
down_revision = 'c20bd2c9b35'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'campaign_action', sa.Column('icon', sa.Unicode(length=20), nullable=True)
    )
    op.add_column('campaign_action', sa.Column('seq', sa.Integer(), nullable=False))


def downgrade():
    op.drop_column('campaign_action', 'seq')
    op.drop_column('campaign_action', 'icon')
