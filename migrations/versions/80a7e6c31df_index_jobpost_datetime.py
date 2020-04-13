# -*- coding: utf-8 -*-
"""Index JobPost.datetime

Revision ID: 80a7e6c31df
Revises: 2c1dec2d1dc5
Create Date: 2015-01-10 19:27:48.703989

"""

# revision identifiers, used by Alembic.
revision = '80a7e6c31df'
down_revision = '2c1dec2d1dc5'

from alembic import op


def upgrade():
    op.create_index(op.f('ix_jobpost_datetime'), 'jobpost', ['datetime'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_jobpost_datetime'), table_name='jobpost')
