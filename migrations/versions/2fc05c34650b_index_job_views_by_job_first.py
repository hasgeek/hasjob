# -*- coding: utf-8 -*-
"""Index job views by job first

Revision ID: 2fc05c34650b
Revises: 3ac38e8fc78b
Create Date: 2015-01-08 21:59:24.614678

"""

# revision identifiers, used by Alembic.
revision = '2fc05c34650b'
down_revision = '3ac38e8fc78b'

from alembic import op


def upgrade():
    op.drop_constraint('userjobview_pkey', 'userjobview', type_='primary')
    op.create_primary_key('userjobview_pkey', 'userjobview', ['jobpost_id', 'user_id'])


def downgrade():
    op.drop_constraint('userjobview_pkey', 'userjobview', type_='primary')
    op.create_primary_key('userjobview_pkey', 'userjobview', ['user_id', 'jobpost_id'])
