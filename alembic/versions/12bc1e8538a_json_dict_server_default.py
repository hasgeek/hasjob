"""JSON Dict server default

Revision ID: 12bc1e8538a
Revises: f66e99eb9f7
Create Date: 2015-01-28 18:41:30.124422

"""

# revision identifiers, used by Alembic.
revision = '12bc1e8538a'
down_revision = 'f66e99eb9f7'

from alembic import op


def upgrade():
    op.alter_column('campaign_action', 'form', server_default='{}')
    op.alter_column('campaign_user_action', 'data', server_default='{}')


def downgrade():
    op.alter_column('campaign_user_action', 'data', server_default=None)
    op.alter_column('campaign_action', 'form', server_default=None)
