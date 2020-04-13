# -*- coding: utf-8 -*-
"""Job impressions

Revision ID: 1ea37e8afd8
Revises: 4d17424a3925
Create Date: 2015-02-17 12:05:00.702713

"""

# revision identifiers, used by Alembic.
revision = '1ea37e8afd8'
down_revision = '4d17424a3925'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'job_impression',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('jobpost_id', sa.Integer(), nullable=False),
        sa.Column('event_session_id', sa.Integer(), nullable=False),
        sa.Column('pinned', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['event_session_id'], ['event_session.id']),
        sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id']),
        sa.PrimaryKeyConstraint('jobpost_id', 'event_session_id'),
    )
    op.create_index(
        op.f('ix_job_impression_event_session_id'),
        'job_impression',
        ['event_session_id'],
        unique=False,
    )
    op.drop_index('ix_starred_job_jobpost_id', table_name='starred_job')


def downgrade():
    op.create_index(
        'ix_starred_job_jobpost_id', 'starred_job', ['jobpost_id'], unique=False
    )
    op.drop_index(
        op.f('ix_job_impression_event_session_id'), table_name='job_impression'
    )
    op.drop_table('job_impression')
