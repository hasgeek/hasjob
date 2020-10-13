"""apphash

Revision ID: 4f639a4a5fc3
Revises: 499df876f3f2
Create Date: 2013-09-13 03:47:23.300046

"""

# revision identifiers, used by Alembic.
revision = '4f639a4a5fc3'
down_revision = '499df876f3f2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'job_application', sa.Column('hashid', sa.String(length=40), nullable=False)
    )
    op.create_unique_constraint(
        'uq_job_application_hashid', 'job_application', ['hashid']
    )
    op.alter_column(
        'job_application', 'message', existing_type=sa.TEXT(), nullable=False
    )


def downgrade():
    op.alter_column(
        'job_application', 'message', existing_type=sa.TEXT(), nullable=True
    )
    op.drop_column('job_application', 'hashid')
