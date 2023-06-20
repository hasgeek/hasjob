"""created_updated_serverdefaults

Revision ID: d286e09aee1
Revises: 41d839fcecb4
Create Date: 2013-09-12 20:26:55.258656

"""

# revision identifiers, used by Alembic.
revision = 'd286e09aee1'
down_revision = '41d839fcecb4'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.alter_column('jobcategory', 'created_at', server_default=None)
    op.alter_column('jobcategory', 'updated_at', server_default=None)
    op.alter_column('jobtype', 'created_at', server_default=None)
    op.alter_column('jobtype', 'updated_at', server_default=None)
    op.alter_column('reportcode', 'created_at', server_default=None)
    op.alter_column('reportcode', 'updated_at', server_default=None)
    op.alter_column('jobpost', 'updated_at', server_default=None)


def downgrade():
    op.alter_column('jobpost', 'updated_at', server_default=sa.func.now())
    op.alter_column('reportcode', 'updated_at', server_default=sa.func.now())
    op.alter_column('reportcode', 'created_at', server_default=sa.func.now())
    op.alter_column('jobtype', 'updated_at', server_default=sa.func.now())
    op.alter_column('jobtype', 'created_at', server_default=sa.func.now())
    op.alter_column('jobcategory', 'updated_at', server_default=sa.func.now())
    op.alter_column('jobcategory', 'created_at', server_default=sa.func.now())
