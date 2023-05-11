"""Use UUID key for event sessions

Revision ID: 57da2d78c9ca
Revises: 375bb2e7a4cc
Create Date: 2016-04-02 14:26:08.883656

"""

# revision identifiers, used by Alembic.
revision = '57da2d78c9ca'
down_revision = '375bb2e7a4cc'

from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'event_session',
        sa.Column('uuid', postgresql.UUID(), nullable=True),
    )
    op.create_unique_constraint('event_session_uuid_key', 'event_session', ['uuid'])


def downgrade():
    op.drop_constraint('event_session_uuid_key', 'event_session', type_='unique')
    op.drop_column('event_session', 'uuid')
