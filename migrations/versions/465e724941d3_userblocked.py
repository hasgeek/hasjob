# -*- coding: utf-8 -*-
"""userblocked

Revision ID: 465e724941d3
Revises: 95eacca1a9d
Create Date: 2013-09-12 22:13:57.647552

"""

# revision identifiers, used by Alembic.
revision = '465e724941d3'
down_revision = '95eacca1a9d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'user',
        sa.Column(
            'blocked', sa.Boolean(), nullable=False, server_default=sa.sql.false()
        ),
    )
    op.alter_column('user', 'blocked', server_default=None)


def downgrade():
    op.drop_column('user', 'blocked')
