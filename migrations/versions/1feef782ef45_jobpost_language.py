# -*- coding: utf-8 -*-
"""JobPost language

Revision ID: 1feef782ef45
Revises: ec6faeb2eec
Create Date: 2014-04-02 02:35:53.483588

"""

# revision identifiers, used by Alembic.
revision = '1feef782ef45'
down_revision = 'ec6faeb2eec'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('jobpost', sa.Column('language', sa.CHAR(length=2), nullable=True))


def downgrade():
    op.drop_column('jobpost', 'language')
