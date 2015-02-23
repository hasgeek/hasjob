"""Campaign anon models

Revision ID: 17a5476c8701
Revises: 2d966f2ff84f
Create Date: 2015-02-23 15:35:22.399926

"""

# revision identifiers, used by Alembic.
revision = '17a5476c8701'
down_revision = '2d966f2ff84f'

from alembic import op
import sqlalchemy as sa
from coaster.sqlalchemy import JsonDict


def upgrade():
    op.create_table('campaign_anon_view',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('anon_user_id', sa.Integer(), nullable=False),
        sa.Column('dismissed', sa.Boolean(), nullable=False),
        sa.Column('session_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['anon_user_id'], ['anon_user.id'], ),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaign.id'], ),
        sa.PrimaryKeyConstraint('campaign_id', 'anon_user_id')
        )
    op.create_index(op.f('ix_campaign_anon_view_anon_user_id'), 'campaign_anon_view', ['anon_user_id'], unique=False)
    op.create_table('campaign_event_session',
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('event_session_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaign.id'], ),
        sa.ForeignKeyConstraint(['event_session_id'], ['event_session.id'], ),
        sa.PrimaryKeyConstraint('campaign_id', 'event_session_id')
        )
    op.create_index(op.f('ix_campaign_event_session_event_session_id'), 'campaign_event_session', ['event_session_id'],
        unique=False)
    op.create_table('campaign_anon_user_action',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('action_id', sa.Integer(), nullable=False),
        sa.Column('anon_user_id', sa.Integer(), nullable=False),
        sa.Column('ipaddr', sa.String(length=45), nullable=True),
        sa.Column('useragent', sa.Unicode(length=250), nullable=True),
        sa.Column('data', JsonDict(), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['action_id'], ['campaign_action.id'], ),
        sa.ForeignKeyConstraint(['anon_user_id'], ['anon_user.id'], ),
        sa.PrimaryKeyConstraint('action_id', 'anon_user_id')
        )
    op.create_index(op.f('ix_campaign_anon_user_action_anon_user_id'), 'campaign_anon_user_action', ['anon_user_id'],
        unique=False)
    op.add_column('campaign_view', sa.Column('session_count', sa.Integer(), nullable=False,
        server_default=sa.text('0')))
    op.alter_column('campaign_view', 'session_count', server_default=None)


def downgrade():
    op.drop_column('campaign_view', 'session_count')
    op.drop_index(op.f('ix_campaign_anon_user_action_anon_user_id'), table_name='campaign_anon_user_action')
    op.drop_table('campaign_anon_user_action')
    op.drop_index(op.f('ix_campaign_event_session_event_session_id'), table_name='campaign_event_session')
    op.drop_table('campaign_event_session')
    op.drop_index(op.f('ix_campaign_anon_view_anon_user_id'), table_name='campaign_anon_view')
    op.drop_table('campaign_anon_view')
