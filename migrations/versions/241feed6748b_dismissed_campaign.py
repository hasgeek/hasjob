"""Dismissed campaign

Revision ID: 241feed6748b
Revises: c5bdaccc5f5
Create Date: 2015-01-28 23:38:11.960951

"""

# revision identifiers, used by Alembic.
revision = '241feed6748b'
down_revision = 'c5bdaccc5f5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('campaign_view', sa.Column('dismissed', sa.Boolean(), nullable=False, server_default='0'))
    op.alter_column('campaign_view', 'dismissed', server_default=None)


def downgrade():
    op.drop_column('campaign_view', 'dismissed')
