"""Board auto posting tags

Revision ID: c039166ecc6
Revises: 33de75e55858
Create Date: 2016-03-14 18:22:29.917293

"""

# revision identifiers, used by Alembic.
revision = 'c039166ecc6'
down_revision = '33de75e55858'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('board_auto_tag',
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ),
        sa.ForeignKeyConstraint(['board_id'], ['board.id'], ),
        sa.PrimaryKeyConstraint('tag_id', 'board_id')
        )


def downgrade():
    op.drop_table('board_auto_tag')
