# -*- coding: utf-8 -*-
"""Featured board flag

Revision ID: 1b3f67ef6387
Revises: 17e2b3e7055a
Create Date: 2016-03-20 00:35:41.706341

"""

# revision identifiers, used by Alembic.
revision = '1b3f67ef6387'
down_revision = '17e2b3e7055a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'board', sa.Column('featured', sa.Boolean(), nullable=False, server_default='0')
    )
    op.alter_column('board', 'featured', server_default=None)
    op.create_index('ix_board_featured', 'board', ['featured'])


def downgrade():
    op.drop_index('ix_board_featured', 'board')
    op.drop_column('board', 'featured')
