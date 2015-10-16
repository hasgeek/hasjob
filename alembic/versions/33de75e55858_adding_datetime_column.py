"""Adding datetime column

Revision ID: 33de75e55858
Revises: 525b125ec799
Create Date: 2015-10-10 12:32:39.936107

"""

# revision identifiers, used by Alembic.
revision = '33de75e55858'
down_revision = '525b125ec799'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('campaign_anon_view', sa.Column('datetime', sa.DateTime()), nullable=True, server_default=created_at)
    op.create_index(op.f('ix_campaign_anon_view_datetime'), 'campaign_anon_view', ['datetime'], unique=False)
    op.alter_column('campaign_anon_view', 'datetime', nullable=False, server_default=None)
    op.add_column('campaign_view', sa.Column('datetime', sa.DateTime()), nulable=True, server_default=created_at)
    op.create_index(op.f('ix_campaign_view_datetime'), 'campaign_view', ['datetime'], unique=False)
    op.alter_column('campaign_view', 'datetime', nullable=False, server_default=None)
    op.add_column('job_impression', sa.Column('datetime', sa.DateTime()), nulable=True, server_default=created_at)
    op.create_index(op.f('ix_job_impression_datetime'), 'job_impression', ['datetime'], unique=False)
    op.alter_column('job_impression', 'datetime', nullable=False, server_default=None)
    op.add_column('job_view_session', sa.Column('datetime', sa.DateTime()), nullable=True, server_default=created_at)
    op.create_index(op.f('ix_job_view_session_datetime'), 'job_view_session', ['datetime'], unique=False)
    op.alter_column('job_view_session', 'datetime', nullable=False, server_default=None)


def downgrade():
    op.drop_index(op.f('ix_job_view_session_datetime'), table_name='job_view_session')
    op.drop_column('job_view_session', 'datetime')
    op.drop_index(op.f('ix_job_impression_datetime'), table_name='job_impression')
    op.drop_column('job_impression', 'datetime')
    op.drop_index(op.f('ix_campaign_view_datetime'), table_name='campaign_view')
    op.drop_column('campaign_view', 'datetime')
    op.drop_index(op.f('ix_campaign_anon_view_datetime'), table_name='campaign_anon_view')
    op.drop_column('campaign_anon_view', 'datetime')

