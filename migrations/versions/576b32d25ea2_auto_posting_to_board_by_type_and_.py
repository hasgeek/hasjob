"""Auto posting to board by type and category

Revision ID: 576b32d25ea2
Revises: 57da2d78c9ca
Create Date: 2016-05-02 13:49:16.797507

"""

# revision identifiers, used by Alembic.
revision = '576b32d25ea2'
down_revision = '57da2d78c9ca'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'board_auto_jobcategory',
        sa.Column('jobcategory_id', sa.Integer(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['board_id'], ['board.id']),
        sa.ForeignKeyConstraint(['jobcategory_id'], ['jobcategory.id']),
        sa.PrimaryKeyConstraint('jobcategory_id', 'board_id'),
    )
    op.create_table(
        'board_auto_jobtype',
        sa.Column('jobtype_id', sa.Integer(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['board_id'], ['board.id']),
        sa.ForeignKeyConstraint(['jobtype_id'], ['jobtype.id']),
        sa.PrimaryKeyConstraint('jobtype_id', 'board_id'),
    )
    op.add_column(
        'board', sa.Column('auto_all', sa.Boolean(), nullable=False, server_default='0')
    )
    op.alter_column('board', 'auto_all', server_default=None)


def downgrade():
    op.drop_column('board', 'auto_all')
    op.drop_table('board_auto_jobtype')
    op.drop_table('board_auto_jobcategory')
