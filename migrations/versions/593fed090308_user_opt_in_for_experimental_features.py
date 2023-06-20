"""User opt-in for experimental features

Revision ID: 593fed090308
Revises: 4b4924b0449b
Create Date: 2015-01-15 01:04:15.201788

"""

# revision identifiers, used by Alembic.
revision = '593fed090308'
down_revision = '4b4924b0449b'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column(
        'job_application',
        sa.Column('optin', sa.Boolean(), nullable=False, server_default='0'),
    )
    op.alter_column('job_application', 'optin', server_default=None)


def downgrade():
    op.drop_column('job_application', 'optin')
