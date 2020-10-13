"""Preserve user's name when they apply for a job

Revision ID: 441fd49059e3
Revises: 1feef782ef45
Create Date: 2014-05-16 03:38:52.778752

"""

# revision identifiers, used by Alembic.
revision = '441fd49059e3'
down_revision = '1feef782ef45'

from alembic import op
from sqlalchemy.sql import column, table
import sqlalchemy as sa


def upgrade():
    user = table('user', column('id', sa.Integer), column('fullname', sa.Unicode(250)))

    job_application = table(
        'job_application',
        column('user_id', sa.Integer),
        column('fullname', sa.Unicode(250)),
    )

    op.add_column(
        'job_application',
        sa.Column(
            'fullname',
            sa.Unicode(length=250),
            nullable=False,
            server_default=sa.text("''"),
        ),
    )
    op.execute(
        job_application.update()
        .where(job_application.c.user_id == user.c.id)
        .values(fullname=user.c.fullname)
    )
    op.alter_column('job_application', 'fullname', server_default=None)


def downgrade():
    op.drop_column('job_application', 'fullname')
