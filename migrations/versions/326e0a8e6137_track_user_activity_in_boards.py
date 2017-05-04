"""Track user activity in boards

Revision ID: 326e0a8e6137
Revises: 2c594a115c39
Create Date: 2015-02-01 14:42:38.603422

"""

# revision identifiers, used by Alembic.
revision = '326e0a8e6137'
down_revision = '2c594a115c39'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user_active_at', sa.Column('board_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_user_active_at_board_id'), 'user_active_at', ['board_id'], unique=False)
    op.create_foreign_key('user_active_at_board_id', 'user_active_at', 'board', ['board_id'], ['id'])


def downgrade():
    op.drop_constraint('user_active_at_board_id', 'user_active_at', type_='foreignkey')
    op.drop_index(op.f('ix_user_active_at_board_id'), table_name='user_active_at')
    op.drop_column('user_active_at', 'board_id')
