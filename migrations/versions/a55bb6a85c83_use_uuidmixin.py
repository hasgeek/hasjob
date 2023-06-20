"""Use UuidMixin

Revision ID: a55bb6a85c83
Revises: 15aede1ebe6f
Create Date: 2017-07-13 14:23:03.655538

"""

# revision identifiers, used by Alembic.
revision = 'a55bb6a85c83'
down_revision = '15aede1ebe6f'

from uuid import uuid4

import progressbar.widgets
import sqlalchemy as sa
from alembic import op
from progressbar import ProgressBar
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import column, table

event_session = table(
    'event_session', column('id', sa.Integer()), column('uuid', postgresql.UUID())
)


def get_progressbar(label, maxval):
    return ProgressBar(
        maxval=maxval,
        widgets=[
            label,
            ': ',
            progressbar.widgets.Percentage(),
            ' ',
            progressbar.widgets.Bar(),
            ' ',
            progressbar.widgets.ETA(),
            ' ',
        ],
    )


def upgrade():
    conn = op.get_bind()
    count = conn.scalar(
        sa.select(sa.func.count('*'))
        .select_from(event_session)
        .where(event_session.c.uuid.is_(None))
    )
    progress = get_progressbar("UUIDs", count)
    progress.start()
    items = conn.execute(
        sa.select(event_session.c.id).where(event_session.c.uuid.is_(None))
    )
    for counter, item in enumerate(items):
        conn.execute(
            sa.update(event_session)
            .where(event_session.c.id == item.id)
            .values(uuid=uuid4())
        )
        progress.update(counter)
    progress.finish()
    op.alter_column(
        'event_session', 'uuid', existing_type=postgresql.UUID(), nullable=False
    )


def downgrade():
    op.alter_column(
        'event_session', 'uuid', existing_type=postgresql.UUID(), nullable=True
    )
