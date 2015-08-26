"""Coin toss column for A/B testing

Revision ID: 525b125ec799
Revises: 5d4d936e9c
Create Date: 2015-08-06 19:18:17.228749

"""

# revision identifiers, used by Alembic.
revision = '525b125ec799'
down_revision = '5d4d936e9c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('job_view_session', sa.Column('cointoss', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('job_view_session', sa.Column('crosstoss', sa.Boolean(), nullable=False, server_default='0'))
    op.alter_column('job_view_session', 'cointoss', server_default=None)
    op.alter_column('job_view_session', 'crosstoss', server_default=None)
    # Update the cointoss and crosstoss columns for existing data
    op.execute(sa.DDL('''
        UPDATE job_view_session SET cointoss=jvs.cointoss, crosstoss=jvs.crosstoss FROM (
            SELECT job_view_session.event_session_id, job_view_session.jobpost_id, TRUE as cointoss,
                CASE WHEN job_impression.bgroup != job_view_session.bgroup AND job_view_session.bgroup IS NOT NULL
                    THEN TRUE ELSE FALSE END AS crosstoss
            FROM job_view_session, job_impression
            WHERE job_view_session.event_session_id = job_impression.event_session_id
                AND job_view_session.jobpost_id = job_impression.jobpost_id
        ) AS jvs
        WHERE job_view_session.event_session_id = jvs.event_session_id
            AND job_view_session.jobpost_id = jvs.jobpost_id;
        '''))


def downgrade():
    op.drop_column('job_view_session', 'crosstoss')
    op.drop_column('job_view_session', 'cointoss')
