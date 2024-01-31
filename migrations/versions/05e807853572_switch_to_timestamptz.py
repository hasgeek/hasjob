"""Switch to timestamptz

Revision ID: 05e807853572
Revises: 625415764254
Create Date: 2019-05-10 12:52:53.016791

"""

# revision identifiers, used by Alembic.
revision = '05e807853572'
down_revision = '625415764254'

from datetime import datetime

import sqlalchemy as sa
from alembic import op

migrate_table_columns = [
    ('anon_job_view', 'created_at'),
    ('anon_user', 'created_at'),
    ('anon_user', 'updated_at'),
    ('board', 'created_at'),
    ('board', 'updated_at'),
    ('board_auto_domain', 'created_at'),
    ('board_auto_domain', 'updated_at'),
    ('board_auto_jobcategory', 'created_at'),
    ('board_auto_jobtype', 'created_at'),
    ('board_auto_location', 'created_at'),
    ('board_auto_location', 'updated_at'),
    ('board_auto_tag', 'created_at'),
    ('board_jobcategory', 'created_at'),
    ('board_jobcategory', 'updated_at'),
    ('board_jobpost', 'created_at'),
    ('board_jobpost', 'updated_at'),
    ('board_jobtype', 'created_at'),
    ('board_jobtype', 'updated_at'),
    ('board_user', 'created_at'),
    ('board_user', 'updated_at'),
    ('campaign', 'created_at'),
    ('campaign', 'end_at'),
    ('campaign', 'start_at'),
    ('campaign', 'updated_at'),
    ('campaign_action', 'created_at'),
    ('campaign_action', 'updated_at'),
    ('campaign_anon_user_action', 'created_at'),
    ('campaign_anon_user_action', 'updated_at'),
    ('campaign_anon_view', 'created_at'),
    ('campaign_anon_view', 'datetime'),
    ('campaign_anon_view', 'last_viewed_at'),
    ('campaign_anon_view', 'reset_at'),
    ('campaign_anon_view', 'updated_at'),
    ('campaign_board', 'created_at'),
    ('campaign_board', 'updated_at'),
    ('campaign_event_session', 'created_at'),
    ('campaign_location', 'created_at'),
    ('campaign_location', 'updated_at'),
    ('campaign_user_action', 'created_at'),
    ('campaign_user_action', 'updated_at'),
    ('campaign_view', 'created_at'),
    ('campaign_view', 'datetime'),
    ('campaign_view', 'last_viewed_at'),
    ('campaign_view', 'reset_at'),
    ('campaign_view', 'updated_at'),
    ('domain', 'banned_at'),
    ('domain', 'created_at'),
    ('domain', 'updated_at'),
    ('event_session', 'active_at'),
    ('event_session', 'created_at'),
    ('event_session', 'ended_at'),
    ('event_session', 'updated_at'),
    ('filterset', 'created_at'),
    ('filterset', 'updated_at'),
    ('filterset_domain', 'created_at'),
    ('filterset_jobcategory', 'created_at'),
    ('filterset_jobtype', 'created_at'),
    ('filterset_tag', 'created_at'),
    ('job_application', 'created_at'),
    ('job_application', 'replied_at'),
    ('job_application', 'updated_at'),
    ('job_location', 'created_at'),
    ('job_location', 'updated_at'),
    ('job_view_session', 'created_at'),
    ('job_view_session', 'datetime'),
    ('job_view_session', 'updated_at'),
    ('jobcategory', 'created_at'),
    ('jobcategory', 'updated_at'),
    ('jobpost', 'closed_datetime'),
    ('jobpost', 'created_at'),
    ('jobpost', 'datetime'),
    ('jobpost', 'review_datetime'),
    ('jobpost', 'updated_at'),
    ('jobpost_admin', 'created_at'),
    ('jobpost_admin', 'updated_at'),
    ('jobpost_tag', 'created_at'),
    ('jobpost_tag', 'updated_at'),
    ('jobpostreport', 'datetime'),
    ('jobtype', 'created_at'),
    ('jobtype', 'updated_at'),
    ('location', 'created_at'),
    ('location', 'updated_at'),
    ('reportcode', 'created_at'),
    ('reportcode', 'updated_at'),
    ('starred_job', 'created_at'),
    ('tag', 'created_at'),
    ('tag', 'updated_at'),
    ('user', 'created_at'),
    ('user', 'updated_at'),
    ('user_active_at', 'active_at'),
    ('userjobview', 'created_at'),
    ('userjobview', 'updated_at'),
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
