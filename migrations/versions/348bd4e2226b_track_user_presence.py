"""Track user presence

Revision ID: 348bd4e2226b
Revises: 33a61e082fb
Create Date: 2015-01-31 05:01:27.691169

"""

# revision identifiers, used by Alembic.
revision = '348bd4e2226b'
down_revision = '33a61e082fb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('user_active_at',
        sa.Column('active_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('active_at', 'user_id')
        )
    op.create_index(op.f('ix_user_active_at_user_id'), 'user_active_at', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_user_active_at_user_id'), table_name='user_active_at')
    op.drop_table('user_active_at')
