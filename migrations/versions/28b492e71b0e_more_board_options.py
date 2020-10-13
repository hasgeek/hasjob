"""More board options

Revision ID: 28b492e71b0e
Revises: 2cd06f7444f8
Create Date: 2014-08-28 03:10:04.720464

"""

# revision identifiers, used by Alembic.
revision = '28b492e71b0e'
down_revision = '2cd06f7444f8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('board', sa.Column('newjob_blurb', sa.UnicodeText(), nullable=True))
    op.add_column(
        'board', sa.Column('newjob_headline', sa.Unicode(length=100), nullable=True)
    )
    op.add_column(
        'board',
        sa.Column('require_login', sa.Boolean(), nullable=False, server_default='1'),
    )
    op.alter_column('board', 'require_login', server_default=None)


def downgrade():
    op.drop_column('board', 'require_login')
    op.drop_column('board', 'newjob_headline')
    op.drop_column('board', 'newjob_blurb')
