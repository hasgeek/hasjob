"""JSON Resume dict

Revision ID: 375bb2e7a4cc
Revises: 1b3f67ef6387
Create Date: 2016-04-02 13:01:25.681813

"""

# revision identifiers, used by Alembic.
revision = '375bb2e7a4cc'
down_revision = '1b3f67ef6387'

import sqlalchemy as sa
from alembic import op

from coaster.sqlalchemy import JsonDict


def upgrade():
    op.add_column(
        'user',
        sa.Column('resume', JsonDict(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.alter_column('user', 'resume', server_default=None)


def downgrade():
    op.drop_column('user', 'resume')
