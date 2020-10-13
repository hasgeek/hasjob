"""Jobpost twitter account

Revision ID: 4bd08758f049
Revises: 1728cf57a9ac
Create Date: 2015-03-09 17:19:20.091090

"""

# revision identifiers, used by Alembic.
revision = '4bd08758f049'
down_revision = '1728cf57a9ac'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('jobpost', sa.Column('twitter', sa.Unicode(length=15), nullable=True))


def downgrade():
    op.drop_column('jobpost', 'twitter')
