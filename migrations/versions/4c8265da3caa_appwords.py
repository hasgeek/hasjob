"""appwords

Revision ID: 4c8265da3caa
Revises: 4f639a4a5fc3
Create Date: 2013-09-15 02:34:56.728020

"""

# revision identifiers, used by Alembic.
revision = '4c8265da3caa'
down_revision = '4f639a4a5fc3'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column(
        'job_application', sa.Column('words', sa.UnicodeText(), nullable=True)
    )


def downgrade():
    op.drop_column('job_application', 'words')
