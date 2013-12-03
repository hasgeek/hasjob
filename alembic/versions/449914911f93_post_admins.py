"""Post admins

Revision ID: 449914911f93
Revises: 2420dd9c9949
Create Date: 2013-12-03 23:03:02.404457

"""

# revision identifiers, used by Alembic.
revision = '449914911f93'
down_revision = '2420dd9c9949'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('jobpost_admin',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('jobpost_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'jobpost_id')
        )


def downgrade():
    op.drop_table('jobpost_admin')
