# -*- coding: utf-8 -*-
"""job_application response statemanager

Revision ID: 625415764254
Revises: 859f6f33c02d
Create Date: 2018-03-24 03:14:19.250467

"""

# revision identifiers, used by Alembic.
revision = '625415764254'
down_revision = '859f6f33c02d'

from alembic import op


def upgrade():
    op.create_check_constraint(
        'job_application_response_check',
        'job_application',
        "response IN (0, 1, 2, 3, 4, 5, 6)",
    )


def downgrade():
    op.drop_constraint('job_application_response_check', 'job_application')
