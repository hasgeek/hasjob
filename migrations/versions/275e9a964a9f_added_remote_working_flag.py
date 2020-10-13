"""Added remote working flag.

Revision ID: 275e9a964a9f
Revises: 28b492e71b0e
Create Date: 2014-11-07 09:43:09.421289

"""

# revision identifiers, used by Alembic.
revision = '275e9a964a9f'
down_revision = '28b492e71b0e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'jobpost',
        sa.Column('remote_location', sa.Boolean, nullable=False, server_default='0'),
    )
    op.alter_column('jobpost', 'remote_location', server_default=None)


def downgrade():
    op.drop_column('jobpost', 'remote_location')
