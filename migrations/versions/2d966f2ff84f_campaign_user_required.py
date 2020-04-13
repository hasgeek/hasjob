# -*- coding: utf-8 -*-
"""Campaign user required

Revision ID: 2d966f2ff84f
Revises: 476608367f85
Create Date: 2015-02-23 09:38:50.323503

"""

# revision identifiers, used by Alembic.
revision = '2d966f2ff84f'
down_revision = '476608367f85'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('campaign', sa.Column('user_required', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('campaign', 'user_required')
