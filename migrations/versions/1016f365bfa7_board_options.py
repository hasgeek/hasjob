"""Board options

Revision ID: 1016f365bfa7
Revises: 504175f63661
Create Date: 2014-08-13 17:36:41.363969

"""

# revision identifiers, used by Alembic.
revision = '1016f365bfa7'
down_revision = '504175f63661'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'board_jobtype',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('jobtype_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['board_id'], ['board.id']),
        sa.ForeignKeyConstraint(['jobtype_id'], ['jobtype.id']),
        sa.PrimaryKeyConstraint('board_id', 'jobtype_id'),
    )
    op.create_table(
        'board_user',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['board_id'], ['board.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('board_id', 'user_id'),
    )
    op.create_table(
        'board_jobcategory',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('jobcategory_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['board_id'], ['board.id']),
        sa.ForeignKeyConstraint(['jobcategory_id'], ['jobcategory.id']),
        sa.PrimaryKeyConstraint('board_id', 'jobcategory_id'),
    )
    op.add_column('board', sa.Column('caption', sa.Unicode(length=250), nullable=True))
    op.add_column(
        'board',
        sa.Column('require_pay', sa.Boolean(), nullable=False, server_default='1'),
    )
    op.alter_column('board', 'require_pay', server_default=None)
    op.add_column(
        'board',
        sa.Column('restrict_listing', sa.Boolean(), nullable=False, server_default='1'),
    )
    op.alter_column('board', 'restrict_listing', server_default=None)


def downgrade():
    op.drop_column('board', 'restrict_listing')
    op.drop_column('board', 'require_pay')
    op.drop_column('board', 'caption')
    op.drop_table('board_jobcategory')
    op.drop_table('board_user')
    op.drop_table('board_jobtype')
