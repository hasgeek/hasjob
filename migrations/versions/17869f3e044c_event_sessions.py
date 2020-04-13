# -*- coding: utf-8 -*-
"""Event sessions

Revision ID: 17869f3e044c
Revises: 326e0a8e6137
Create Date: 2015-02-05 23:27:16.259206

"""

# revision identifiers, used by Alembic.
revision = '17869f3e044c'
down_revision = '326e0a8e6137'

from alembic import op
import sqlalchemy as sa

from coaster.sqlalchemy import JsonDict


def upgrade():
    op.create_table(
        'anon_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_anon_user_user_id'), 'anon_user', ['user_id'], unique=False
    )
    op.create_table(
        'event_session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('anon_user_id', sa.Integer(), nullable=True),
        sa.Column('referrer', sa.Unicode(length=2083), nullable=True),
        sa.Column('utm_source', sa.Unicode(length=250), nullable=False),
        sa.Column('utm_medium', sa.Unicode(length=250), nullable=False),
        sa.Column('utm_term', sa.Unicode(length=250), nullable=False),
        sa.Column('utm_content', sa.Unicode(length=250), nullable=False),
        sa.Column('utm_id', sa.Unicode(length=250), nullable=False),
        sa.Column('utm_campaign', sa.Unicode(length=250), nullable=False),
        sa.Column('gclid', sa.Unicode(length=250), nullable=False),
        sa.Column('active_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            'CASE WHEN (event_session.user_id IS NOT NULL) THEN 1 ELSE 0 END + CASE WHEN (event_session.anon_user_id IS NOT NULL) THEN 1 ELSE 0 END = 1',
            name='user_event_session_user_id_or_anon_user_id',
        ),
        sa.ForeignKeyConstraint(['anon_user_id'], ['anon_user.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_event_session_anon_user_id'),
        'event_session',
        ['anon_user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_event_session_user_id'), 'event_session', ['user_id'], unique=False
    )
    op.create_table(
        'user_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('event_session_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.Unicode(length=2038), nullable=True),
        sa.Column('referrer', sa.Unicode(length=2038), nullable=True),
        sa.Column('method', sa.Unicode(length=10), nullable=True),
        sa.Column('status_code', sa.SmallInteger(), nullable=True),
        sa.Column('name', sa.Unicode(length=80), nullable=False),
        sa.Column('data', JsonDict(), nullable=True),
        sa.ForeignKeyConstraint(['event_session_id'], ['event_session.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('user_event')
    op.drop_index(op.f('ix_event_session_user_id'), table_name='event_session')
    op.drop_index(op.f('ix_event_session_anon_user_id'), table_name='event_session')
    op.drop_table('event_session')
    op.drop_index(op.f('ix_anon_user_user_id'), table_name='anon_user')
    op.drop_table('anon_user')
