"""Save language detection confidence

Revision ID: 4b4924b0449b
Revises: 80a7e6c31df
Create Date: 2015-01-13 20:29:11.922146

"""

# revision identifiers, used by Alembic.
revision = '4b4924b0449b'
down_revision = '80a7e6c31df'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column(
        'jobpost', sa.Column('language_confidence', sa.Float(), nullable=True)
    )


def downgrade():
    op.drop_column('jobpost', 'language_confidence')
