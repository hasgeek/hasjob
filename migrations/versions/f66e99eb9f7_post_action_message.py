# -*- coding: utf-8 -*-
"""Post action message

Revision ID: f66e99eb9f7
Revises: 49b48df19d82
Create Date: 2015-01-28 18:32:44.661697

"""

# revision identifiers, used by Alembic.
revision = 'f66e99eb9f7'
down_revision = '49b48df19d82'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'campaign_action', sa.Column('message', sa.UnicodeText(), nullable=False)
    )


def downgrade():
    op.drop_column('campaign_action', 'message')
