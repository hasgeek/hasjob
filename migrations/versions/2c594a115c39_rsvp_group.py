"""RSVP group

Revision ID: 2c594a115c39
Revises: 23546c6d07e2
Create Date: 2015-02-01 03:38:58.373672

"""

# revision identifiers, used by Alembic.
revision = '2c594a115c39'
down_revision = '23546c6d07e2'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column(
        'campaign_action', sa.Column('group', sa.Unicode(length=20), nullable=True)
    )


def downgrade():
    op.drop_column('campaign_action', 'group')
