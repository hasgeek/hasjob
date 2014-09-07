"""Private types and categories

Revision ID: 2cd06f7444f8
Revises: 1016f365bfa7
Create Date: 2014-08-14 00:07:15.324411

"""

# revision identifiers, used by Alembic.
revision = '2cd06f7444f8'
down_revision = '1016f365bfa7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('jobcategory', sa.Column('private', sa.Boolean(), nullable=False, server_default='0'))
    op.alter_column('jobcategory', 'private', server_default=None)
    op.add_column('jobtype', sa.Column('private', sa.Boolean(), nullable=False, server_default='0'))
    op.alter_column('jobtype', 'private', server_default=None)


def downgrade():
    op.drop_column('jobtype', 'private')
    op.drop_column('jobcategory', 'private')
