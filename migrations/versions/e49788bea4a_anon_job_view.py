"""Anon job view

Revision ID: e49788bea4a
Revises: 5a725fd5ddd6
Create Date: 2015-02-07 01:46:03.956058

"""

# revision identifiers, used by Alembic.
revision = 'e49788bea4a'
down_revision = '5a725fd5ddd6'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table(
        'anon_job_view',
        sa.Column('jobpost_id', sa.Integer(), nullable=False),
        sa.Column('anon_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['anon_user_id'], ['anon_user.id']),
        sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id']),
        sa.PrimaryKeyConstraint('jobpost_id', 'anon_user_id'),
    )
    op.create_index(
        op.f('ix_anon_job_view_anon_user_id'),
        'anon_job_view',
        ['anon_user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_anon_job_view_created_at'),
        'anon_job_view',
        ['created_at'],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f('ix_anon_job_view_created_at'), table_name='anon_job_view')
    op.drop_index(op.f('ix_anon_job_view_anon_user_id'), table_name='anon_job_view')
    op.drop_table('anon_job_view')
