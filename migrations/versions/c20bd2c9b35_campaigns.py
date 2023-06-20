"""Campaigns

Revision ID: c20bd2c9b35
Revises: 29fd6847a8e2
Create Date: 2015-01-28 04:47:42.965122

"""

# revision identifiers, used by Alembic.
revision = 'c20bd2c9b35'
down_revision = '29fd6847a8e2'

import sqlalchemy as sa
from alembic import op

from coaster.sqlalchemy import JsonDict


def upgrade():
    op.create_table(
        'campaign',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('start_at', sa.DateTime(), nullable=False),
        sa.Column('end_at', sa.DateTime(), nullable=False),
        sa.Column('public', sa.Boolean(), nullable=False),
        sa.Column('position', sa.SmallInteger(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('subject', sa.Unicode(length=250), nullable=True),
        sa.Column('blurb', sa.UnicodeText(), nullable=False),
        sa.Column('description', sa.UnicodeText(), nullable=False),
        sa.Column('banner_image', sa.Unicode(length=250), nullable=True),
        sa.Column('banner_location', sa.SmallInteger(), nullable=False),
        sa.Column('name', sa.Unicode(length=250), nullable=False),
        sa.Column('title', sa.Unicode(length=250), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'campaign_board',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['board_id'], ['board.id']),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaign.id']),
        sa.PrimaryKeyConstraint('board_id', 'campaign_id'),
    )
    op.create_index(
        op.f('ix_campaign_board_campaign_id'),
        'campaign_board',
        ['campaign_id'],
        unique=False,
    )
    op.create_table(
        'campaign_view',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaign.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('campaign_id', 'user_id'),
    )
    op.create_table(
        'campaign_location',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('geonameid', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaign.id']),
        sa.PrimaryKeyConstraint('campaign_id', 'geonameid'),
    )
    op.create_index(
        op.f('ix_campaign_location_geonameid'),
        'campaign_location',
        ['geonameid'],
        unique=False,
    )
    op.create_table(
        'campaign_action',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('public', sa.Boolean(), nullable=False),
        sa.Column(
            'type',
            sa.Enum('D', 'F', 'L', 'M', 'N', 'Y', name='campaign_action_type_enum'),
            nullable=False,
        ),
        sa.Column('category', sa.Unicode(length=20), nullable=False),
        sa.Column('link', sa.Unicode(length=250), nullable=True),
        sa.Column('form', JsonDict(), nullable=False),
        sa.Column('name', sa.Unicode(length=250), nullable=False),
        sa.Column('title', sa.Unicode(length=250), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaign.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id', 'name'),
    )
    op.create_table(
        'campaign_user_action',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('action_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('ipaddr', sa.String(length=45), nullable=True),
        sa.Column('useragent', sa.Unicode(length=250), nullable=True),
        sa.Column('data', JsonDict(), nullable=False),
        sa.ForeignKeyConstraint(['action_id'], ['campaign_action.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_campaign_user_action_action_id'),
        'campaign_user_action',
        ['action_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_campaign_user_action_user_id'),
        'campaign_user_action',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_userjobview_user_id'), 'userjobview', ['user_id'], unique=False
    )


def downgrade():
    op.drop_index(op.f('ix_userjobview_user_id'), table_name='userjobview')
    op.drop_index(
        op.f('ix_campaign_user_action_user_id'), table_name='campaign_user_action'
    )
    op.drop_index(
        op.f('ix_campaign_user_action_action_id'), table_name='campaign_user_action'
    )
    op.drop_table('campaign_user_action')
    op.drop_table('campaign_action')
    op.execute(sa.text('DROP TYPE campaign_action_type_enum;'))
    op.drop_index(
        op.f('ix_campaign_location_geonameid'), table_name='campaign_location'
    )
    op.drop_table('campaign_location')
    op.drop_table('campaign_view')
    op.drop_index(op.f('ix_campaign_board_campaign_id'), table_name='campaign_board')
    op.drop_table('campaign_board')
    op.drop_table('campaign')
