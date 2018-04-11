"""schema_changes_for_job_alerts

Revision ID: 41890cdbddf0
Revises: 859f6f33c02d
Create Date: 2018-04-09 20:43:57.810337

"""

# revision identifiers, used by Alembic.
revision = '41890cdbddf0'
down_revision = '859f6f33c02d'

from alembic import op
import sqlalchemy as sa



def upgrade():
    op.create_table('jobpost_subscription',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('filterset_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.Unicode(length=254), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('email_verify_key', sa.String(length=40), nullable=True),
        sa.Column('unsubscribe_key', sa.String(length=40), nullable=True),
        sa.Column('email_verified_at', sa.DateTime(), nullable=True),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('email_frequency', sa.Integer(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['filterset_id'], ['filterset.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email_verify_key'),
        sa.UniqueConstraint('filterset_id', 'email'),
        sa.UniqueConstraint('unsubscribe_key')
    )
    op.create_index(op.f('ix_jobpost_subscription_active'), 'jobpost_subscription', ['active'], unique=False)
    op.create_index(op.f('ix_jobpost_subscription_email_verified_at'), 'jobpost_subscription', ['email_verified_at'], unique=False)

    op.create_table('jobpost_alert',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('jobpost_subscription_id', sa.Integer(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('fail_reason', sa.Unicode(length=255), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['jobpost_subscription_id'], ['jobpost_subscription.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobpost_alert_jobpost_subscription_id'), 'jobpost_alert', ['jobpost_subscription_id'], unique=False)

    op.create_table('jobpost_jobpost_alert',
        sa.Column('jobpost_id', sa.Integer(), nullable=False),
        sa.Column('jobpost_alert_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['jobpost_alert_id'], ['jobpost_alert.id'], ),
        sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id'], ),
        sa.PrimaryKeyConstraint('jobpost_id', 'jobpost_alert_id')
    )
    op.add_column(u'filterset', sa.Column('sitemap', sa.Boolean(), nullable=True))
    op.create_index(op.f('ix_filterset_sitemap'), 'filterset', ['sitemap'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_filterset_sitemap'), table_name='filterset')
    op.drop_column(u'filterset', 'sitemap')
    op.drop_table('jobpost_jobpost_alert')
    op.drop_index(op.f('ix_jobpost_alert_jobpost_subscription_id'), table_name='jobpost_alert')
    op.drop_table('jobpost_alert')
    op.drop_index(op.f('ix_jobpost_subscription_email_verified_at'), table_name='jobpost_subscription')
    op.drop_index(op.f('ix_jobpost_subscription_active'), table_name='jobpost_subscription')
    op.drop_table('jobpost_subscription')
