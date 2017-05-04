"""Switch to UserBase2

Revision ID: 260571e00aef
Revises: 3fc1aa06cbeb
Create Date: 2014-06-26 19:45:04.842343

"""

# revision identifiers, used by Alembic.
revision = '260571e00aef'
down_revision = '3fc1aa06cbeb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('status', sa.Integer(), nullable=False, server_default=sa.text('0')))
    op.alter_column('user', 'status', server_default=None)


def downgrade():
    op.drop_column('user', 'status')
