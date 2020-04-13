# -*- coding: utf-8 -*-
"""Domain banned at

Revision ID: 15aede1ebe6f
Revises: da1dfcda8b3
Create Date: 2016-07-07 13:35:04.041999

"""

# revision identifiers, used by Alembic.
revision = '15aede1ebe6f'
down_revision = 'da1dfcda8b3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('domain', sa.Column('banned_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('domain', 'banned_at')
