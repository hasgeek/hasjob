"""Tweet id for JobPost

Revision ID: d8258df712fa
Revises: 625415764254
Create Date: 2018-07-12 18:22:20.245244

"""

# revision identifiers, used by Alembic.
revision = 'd8258df712fa'
down_revision = '625415764254'

from alembic import op
import sqlalchemy as sa



def upgrade():
    op.add_column('jobpost', sa.Column('tweetid', sa.Unicode(length=30), nullable=True))


def downgrade():
    op.drop_column('jobpost', 'tweetid')
