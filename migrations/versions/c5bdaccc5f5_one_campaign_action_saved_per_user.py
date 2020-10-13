"""One campaign action saved per user

Revision ID: c5bdaccc5f5
Revises: 12bc1e8538a
Create Date: 2015-01-28 21:57:01.617117

"""

# revision identifiers, used by Alembic.
revision = 'c5bdaccc5f5'
down_revision = '12bc1e8538a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_index(
        'ix_campaign_user_action_action_id', table_name='campaign_user_action'
    )
    op.drop_constraint(
        'campaign_user_action_pkey', 'campaign_user_action', type_='primary'
    )
    op.drop_column('campaign_user_action', 'id')
    op.create_primary_key(
        'campaign_user_action_pkey', 'campaign_user_action', ['action_id', 'user_id']
    )


def downgrade():
    op.drop_constraint(
        'campaign_user_action_pkey', 'campaign_user_action', type_='primary'
    )
    op.add_column('campaign_user_action', sa.Column('id', sa.INTEGER(), nullable=False))
    op.create_primary_key('campaign_user_action_pkey', 'campaign_user_action', ['id'])
    op.create_index(
        'ix_campaign_user_action_action_id',
        'campaign_user_action',
        ['action_id'],
        unique=False,
    )
