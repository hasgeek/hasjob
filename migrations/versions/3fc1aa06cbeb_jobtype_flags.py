# -*- coding: utf-8 -*-
"""JobType flags

Revision ID: 3fc1aa06cbeb
Revises: 434344d0a2d0
Create Date: 2014-06-19 23:29:23.643414

"""

# revision identifiers, used by Alembic.
revision = '3fc1aa06cbeb'
down_revision = '434344d0a2d0'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'jobtype',
        sa.Column('nopay_allowed', sa.Boolean(), nullable=False, server_default='True'),
    )
    op.add_column(
        'jobtype',
        sa.Column(
            'webmail_allowed', sa.Boolean(), nullable=False, server_default='True'
        ),
    )
    op.alter_column('jobtype', 'nopay_allowed', server_default=None)
    op.alter_column('jobtype', 'webmail_allowed', server_default=None)


def downgrade():
    op.drop_column('jobtype', 'webmail_allowed')
    op.drop_column('jobtype', 'nopay_allowed')
