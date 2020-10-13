"""Index fkey to user

Revision ID: 4616e70f18f4
Revises: 5269eb17ff82
Create Date: 2015-01-31 03:05:19.836389

"""

# revision identifiers, used by Alembic.
revision = '4616e70f18f4'
down_revision = '5269eb17ff82'

from alembic import op


def upgrade():
    op.create_index(
        op.f('ix_job_application_replied_by_id'),
        'job_application',
        ['replied_by_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_job_application_user_id'), 'job_application', ['user_id'], unique=False
    )
    op.create_index(op.f('ix_jobpost_org_id'), 'jobpost', ['org_id'], unique=False)
    op.create_index(
        op.f('ix_jobpost_reviewer_id'), 'jobpost', ['reviewer_id'], unique=False
    )
    op.create_index(op.f('ix_jobpost_user_id'), 'jobpost', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_jobpost_user_id'), table_name='jobpost')
    op.drop_index(op.f('ix_jobpost_reviewer_id'), table_name='jobpost')
    op.drop_index(op.f('ix_jobpost_org_id'), table_name='jobpost')
    op.drop_index(op.f('ix_job_application_user_id'), table_name='job_application')
    op.drop_index(
        op.f('ix_job_application_replied_by_id'), table_name='job_application'
    )
