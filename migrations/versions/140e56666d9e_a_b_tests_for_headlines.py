"""A/B tests for headlines

Revision ID: 140e56666d9e
Revises: 1ea37e8afd8
Create Date: 2015-02-18 21:18:29.532007

"""

# revision identifiers, used by Alembic.
revision = '140e56666d9e'
down_revision = '1ea37e8afd8'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table(
        'job_view_session',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('event_session_id', sa.Integer(), nullable=False),
        sa.Column('jobpost_id', sa.Integer(), nullable=False),
        sa.Column('bgroup', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['event_session_id'], ['event_session.id']),
        sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id']),
        sa.PrimaryKeyConstraint('event_session_id', 'jobpost_id'),
    )
    op.create_index(
        op.f('ix_job_view_session_jobpost_id'),
        'job_view_session',
        ['jobpost_id'],
        unique=False,
    )
    op.add_column('job_impression', sa.Column('bgroup', sa.Boolean(), nullable=True))
    op.add_column(
        'jobpost', sa.Column('headlineb', sa.Unicode(length=100), nullable=True)
    )


def downgrade():
    op.drop_column('jobpost', 'headlineb')
    op.drop_column('job_impression', 'bgroup')
    op.drop_index(
        op.f('ix_job_view_session_event_session_id'), table_name='job_view_session'
    )
    op.drop_table('job_view_session')
