"""fullname

Revision ID: 1bcc4e025b04
Revises: 30828b49527
Create Date: 2013-08-30 12:08:23.561163

"""

# revision identifiers, used by Alembic.
revision = '1bcc4e025b04'
down_revision = '30828b49527'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'jobpost', sa.Column('fullname', sa.Unicode(length=80), nullable=True)
    )


def downgrade():
    op.drop_column('jobpost', 'fullname')
