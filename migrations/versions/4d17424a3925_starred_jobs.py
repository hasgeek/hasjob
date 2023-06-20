"""Starred jobs

Revision ID: 4d17424a3925
Revises: e49788bea4a
Create Date: 2015-02-13 16:02:29.299251

"""

# revision identifiers, used by Alembic.
revision = '4d17424a3925'
down_revision = 'e49788bea4a'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table(
        'starred_job',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('jobpost_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('user_id', 'jobpost_id'),
    )
    op.create_index(
        op.f('ix_starred_job_jobpost_id'), 'starred_job', ['jobpost_id'], unique=False
    )


def downgrade():
    op.drop_index(op.f('ix_starred_job_jobpost_id'), table_name='starred_job')
    op.drop_table('starred_job')
