"""jobpost state constraint

Revision ID: b26b524d3fba
Revises: a55bb6a85c83
Create Date: 2018-02-21 22:34:38.051604

"""

# revision identifiers, used by Alembic.
revision = 'b26b524d3fba'
down_revision = '8a37fe07ef9d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_check_constraint(
        'jobpost_state_check',
        'jobpost',
        "status IN (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)"
    )


def downgrade():
    op.drop_constraint(
        'jobpost_state_check',
        'jobpost'
    )
