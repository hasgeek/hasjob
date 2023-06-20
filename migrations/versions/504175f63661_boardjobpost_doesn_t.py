"""BoardJobPost doesn't need its own primary key

Revision ID: 504175f63661
Revises: 260571e00aef
Create Date: 2014-08-11 01:45:37.350830

"""

# revision identifiers, used by Alembic.
revision = '504175f63661'
down_revision = '260571e00aef'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.drop_column('board_jobpost', 'id')
    op.create_primary_key(
        'board_jobpost_pkey', 'board_jobpost', ['board_id', 'jobpost_id']
    )


def downgrade():
    op.drop_constraint('board_jobpost_pkey', 'board_jobpost')
    op.add_column(
        'board_jobpost', sa.Column('id', sa.INTEGER(), primary_key=True, nullable=False)
    )
