"""Boards

Revision ID: 472ca8e93765
Revises: 470c8feb73cc
Create Date: 2014-02-13 02:40:42.772517

"""

# revision identifiers, used by Alembic.
revision = '472ca8e93765'
down_revision = '470c8feb73cc'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table(
        'board',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('userid', sa.Unicode(length=22), nullable=False),
        sa.Column('description', sa.UnicodeText(), nullable=False),
        sa.Column('name', sa.Unicode(length=250), nullable=False),
        sa.Column('title', sa.Unicode(length=250), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('userid'),
    )
    op.create_table(
        'board_jobpost',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('jobpost_id', sa.Integer(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('pinned', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['board_id'], ['board.id']),
        sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('board_jobpost')
    op.drop_table('board')
