"""created_at is not nullable

Revision ID: d19802512a1
Revises: 576b32d25ea2
Create Date: 2016-05-02 21:55:52.179708

"""

# revision identifiers, used by Alembic.
revision = 'd19802512a1'
down_revision = '576b32d25ea2'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.alter_column(
        'board_auto_jobcategory',
        'created_at',
        existing_type=sa.DateTime(),
        nullable=False,
    )
    op.alter_column(
        'board_auto_jobtype', 'created_at', existing_type=sa.DateTime(), nullable=False
    )
    op.alter_column(
        'board_auto_tag', 'created_at', existing_type=sa.DateTime(), nullable=False
    )
    op.alter_column(
        'campaign_event_session',
        'created_at',
        existing_type=sa.DateTime(),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        'campaign_event_session',
        'created_at',
        existing_type=sa.DateTime(),
        nullable=True,
    )
    op.alter_column(
        'board_auto_tag', 'created_at', existing_type=sa.DateTime(), nullable=True
    )
    op.alter_column(
        'board_auto_jobtype', 'created_at', existing_type=sa.DateTime(), nullable=True
    )
    op.alter_column(
        'board_auto_jobcategory',
        'created_at',
        existing_type=sa.DateTime(),
        nullable=True,
    )
