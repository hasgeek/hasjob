"""Employer response message

Revision ID: 2420dd9c9949
Revises: 3e27bf9706ee
Create Date: 2013-11-25 15:06:46.015614

"""

# revision identifiers, used by Alembic.
revision = '2420dd9c9949'
down_revision = '3e27bf9706ee'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'job_application',
        sa.Column('response_message', sa.UnicodeText(), nullable=True),
    )


def downgrade():
    op.drop_column('job_application', 'response_message')
