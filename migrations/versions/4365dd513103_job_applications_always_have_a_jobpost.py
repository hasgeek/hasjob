# -*- coding: utf-8 -*-
"""Job applications always have a jobpost

Revision ID: 4365dd513103
Revises: 2fc05c34650b
Create Date: 2015-01-09 00:02:23.010069

"""

# revision identifiers, used by Alembic.
revision = '4365dd513103'
down_revision = '2fc05c34650b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column(
        'job_application', 'jobpost_id', existing_type=sa.INTEGER(), nullable=False
    )


def downgrade():
    op.alter_column(
        'job_application', 'jobpost_id', existing_type=sa.INTEGER(), nullable=True
    )
