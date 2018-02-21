"""jobpost state constraint

Revision ID: b26b524d3fba
Revises: a55bb6a85c83
Create Date: 2018-02-21 22:34:38.051604

"""

# revision identifiers, used by Alembic.
revision = 'b26b524d3fba'
down_revision = 'a55bb6a85c83'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_check_constraint(
        'ck_jobpost_state_valid',
        'jobpost',
        'status IN (9, 6, 7, 2, 4, 3, 0, 10, 8, 5, 1)'
    )


def downgrade():
    op.drop_constraint(
        'ck_jobpost_state_valid',
        'jobpost'
    )
