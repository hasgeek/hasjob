# -*- coding: utf-8 -*-
"""JobApplication.replied_by

Revision ID: 470c8feb73cc
Revises: 449914911f93
Create Date: 2013-12-14 22:32:49.982184

"""

# revision identifiers, used by Alembic.
revision = '470c8feb73cc'
down_revision = '449914911f93'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'job_application', sa.Column('replied_by_id', sa.Integer(), nullable=True)
    )


def downgrade():
    op.drop_column('job_application', 'replied_by_id')
