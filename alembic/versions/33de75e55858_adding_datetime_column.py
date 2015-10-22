"""Adding datetime column

Revision ID: 33de75e55858
Revises: 525b125ec799
Create Date: 2015-10-10 12:32:39.936107

"""

# revision identifiers, used by Alembic.
revision = '33de75e55858'
down_revision = '525b125ec799'


from sqlalchemy.sql import table, column

from alembic import op
import sqlalchemy as sa


def upgrade():
    campaign_anon_view = table('campaign_anon_view',
	column('created_at', sa.DateTime),
	column('datetime', sa.DateTime))
    op.add_column('campaign_anon_view', sa.Column('datetime', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.execute(campaign_anon_view.update().values(datetime=campaign_anon_view.c.created_at))
    op.alter_column('campaign_anon_view', 'datetime', server_default=None)

    campaign_view = table('campaign_view',
	column('created_at', sa.DateTime),
	column('datetime', sa.DateTime))
    op.add_column('campaign_view', sa.Column('datetime', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.execute(campaign_view.update().values(datetime=campaign_view.c.created_at))
    op.alter_column('campaign_view', 'datetime', server_default=None)

    job_impression = table('job_impression',
	column('created_at', sa.DateTime),
	column('datetime', sa.DateTime))
    op.add_column('job_impression', sa.Column('datetime', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.execute(job_impression.update().values(datetime=job_impression.c.created_at))
    op.alter_column('job_impression', 'datetime', server_default=None)
    
    job_view_session = table('job_view_session',
	column('created_at', sa.DateTime),
	column('datetime', sa.DateTime))
    op.add_column('job_view_session', sa.Column('datetime', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.execute(job_view_session.update().values(datetime=job_view_session.c.created_at))
    op.alter_column('job_view_session', 'datetime', server_default=None)


def downgrade():
    op.drop_column('job_view_session', 'datetime')
    op.drop_column('job_impression', 'datetime')
    op.drop_column('campaign_view', 'datetime')
    op.drop_column('campaign_anon_view', 'datetime')

