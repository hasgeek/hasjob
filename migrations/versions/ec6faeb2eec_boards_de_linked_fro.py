"""Boards de-linked from organizations

Revision ID: ec6faeb2eec
Revises: 34e1d4b2f636
Create Date: 2014-03-28 19:59:52.118155

"""

# revision identifiers, used by Alembic.
revision = 'ec6faeb2eec'
down_revision = '34e1d4b2f636'

from alembic import op


def upgrade():
    op.drop_constraint('board_userid_key', 'board')
    op.create_index('ix_board_userid', 'board', ['userid'])


def downgrade():
    op.drop_index('ix_board_userid', 'board')
    op.create_unique_constraint('board_userid_key', 'board', ['userid'])
