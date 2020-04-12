# -*- coding: utf-8 -*-
"""Org teams

Revision ID: 29fd6847a8e2
Revises: c55612fb52a
Create Date: 2015-01-27 03:02:47.553438

"""

# revision identifiers, used by Alembic.
revision = '29fd6847a8e2'
down_revision = 'c55612fb52a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'team',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('title', sa.Unicode(length=250), nullable=False),
        sa.Column('userid', sa.String(length=22), nullable=False),
        sa.Column('owners', sa.Boolean(), nullable=False),
        sa.Column('orgid', sa.String(length=22), nullable=False),
        sa.Column('members', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('userid'),
    )
    op.create_index(op.f('ix_team_orgid'), 'team', ['orgid'], unique=False)
    op.create_table(
        'users_teams',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['team.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('user_id', 'team_id'),
    )
    op.add_column(
        'organization', sa.Column('admin_team_id', sa.Integer(), nullable=True)
    )
    op.add_column(
        'organization', sa.Column('hiring_team_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'organization_admin_team_id_fkey',
        'organization',
        'team',
        ['admin_team_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'organization_hiring_team_id_fkey',
        'organization',
        'team',
        ['hiring_team_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade():
    op.drop_constraint(
        'organization_hiring_team_id_fkey', 'organization', type_='foreignkey'
    )
    op.drop_constraint(
        'organization_admin_team_id_fkey', 'organization', type_='foreignkey'
    )
    op.drop_column('organization', 'hiring_team_id')
    op.drop_column('organization', 'admin_team_id')
    op.drop_table('users_teams')
    op.drop_index(op.f('ix_team_orgid'), table_name='team')
    op.drop_table('team')
