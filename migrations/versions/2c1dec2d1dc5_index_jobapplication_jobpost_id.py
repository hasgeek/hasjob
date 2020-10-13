"""Index JobApplication.jobpost_id

Revision ID: 2c1dec2d1dc5
Revises: 4365dd513103
Create Date: 2015-01-09 00:06:47.945256

"""

# revision identifiers, used by Alembic.
revision = '2c1dec2d1dc5'
down_revision = '4365dd513103'

from alembic import op


def upgrade():
    op.create_index(
        op.f('ix_job_application_jobpost_id'),
        'job_application',
        ['jobpost_id'],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f('ix_job_application_jobpost_id'), table_name='job_application')
