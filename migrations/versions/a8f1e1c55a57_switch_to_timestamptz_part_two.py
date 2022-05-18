"""Switch to timestamptz, part two

Revision ID: a8f1e1c55a57
Revises: 05e807853572
Create Date: 2019-05-15 20:46:26.193463

"""


# revision identifiers, used by Alembic.
revision = 'a8f1e1c55a57'
down_revision = '05e807853572'

from datetime import datetime

from alembic import op
import sqlalchemy as sa

migrate_table_columns = [
    ('job_impression', 'created_at'),
    ('job_impression', 'datetime'),
    ('job_impression', 'updated_at'),
    ('user_event', 'created_at'),
    ('user_event', 'updated_at'),
]


def upgrade():
    for table, column in migrate_table_columns:
        now = datetime.now()  # Local time
        print(  # noqa: T201
            "{}: {}.{}".format(now.strftime('%Y-%m-%d %T'), table, column)
        )
        op.execute(
            sa.DDL(
                'ALTER TABLE "%(table)s" ALTER COLUMN "%(column)s" TYPE TIMESTAMP WITH TIME ZONE USING "%(column)s" AT TIME ZONE \'UTC\'',
                context={'table': table, 'column': column},
            )
        )
        print('...%s' % str(datetime.now() - now))  # noqa: T201


def downgrade():
    for table, column in reversed(migrate_table_columns):
        now = datetime.now()  # Local time
        print(  # noqa: T201
            "{}: {}.{}".format(now.strftime('%Y-%m-%d %T'), table, column)
        )
        op.execute(
            sa.DDL(
                'ALTER TABLE "%(table)s" ALTER COLUMN "%(column)s" TYPE TIMESTAMP WITHOUT TIME ZONE',
                context={'table': table, 'column': column},
            )
        )
        print('...%s' % str(datetime.now() - now))  # noqa: T201
