# -*- coding: utf-8 -*-
"""Additional columns

Revision ID: 5a725fd5ddd6
Revises: 17869f3e044c
Create Date: 2015-02-06 02:11:00.632249

"""

# revision identifiers, used by Alembic.
revision = '5a725fd5ddd6'
down_revision = '17869f3e044c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'user_event', sa.Column('ipaddr', sa.Unicode(length=45), nullable=True)
    )
    op.add_column(
        'user_event', sa.Column('useragent', sa.Unicode(length=250), nullable=True)
    )


def downgrade():
    op.drop_column('user_event', 'useragent')
    op.drop_column('user_event', 'ipaddr')
