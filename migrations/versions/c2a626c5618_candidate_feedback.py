"""Candidate feedback

Revision ID: c2a626c5618
Revises: 593fed090308
Create Date: 2015-01-20 13:23:57.220096

"""

# revision identifiers, used by Alembic.
revision = 'c2a626c5618'
down_revision = '593fed090308'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('job_application', sa.Column('candidate_feedback', sa.SmallInteger(), nullable=True))


def downgrade():
    op.drop_column('job_application', 'candidate_feedback')
