"""schema_changes_for_job_alerts

Revision ID: 62a7a0ded059
Revises: 625415764254
Create Date: 2018-04-11 14:37:35.020056

"""

# revision identifiers, used by Alembic.
revision = '62a7a0ded059'
down_revision = '625415764254'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('jobpost_subscription',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('filterset_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.Unicode(length=254), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('anon_user_id', sa.Integer(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('email_verify_key', sa.String(length=40), nullable=True),
        sa.Column('unsubscribe_key', sa.String(length=40), nullable=True),
        sa.Column('subscribed_at', sa.DateTime(), nullable=False),
        sa.Column('email_verified_at', sa.DateTime(), nullable=True),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('email_frequency', sa.Integer(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.CheckConstraint(u'CASE WHEN (user_id IS NOT NULL) THEN 1 ELSE 0 END + CASE WHEN (anon_user_id IS NOT NULL) THEN 1 ELSE 0 END <= 1', name='jobpost_subscription_user_id_or_anon_user_id'),
        sa.ForeignKeyConstraint(['anon_user_id'], ['anon_user.id'], ),
        sa.ForeignKeyConstraint(['filterset_id'], ['filterset.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email_verify_key'),
        sa.UniqueConstraint('filterset_id', 'email'),
        sa.UniqueConstraint('unsubscribe_key')
    )
    op.create_index(op.f('ix_jobpost_subscription_active'), 'jobpost_subscription', ['active'], unique=False)
    op.create_index(op.f('ix_jobpost_subscription_anon_user_id'), 'jobpost_subscription', ['anon_user_id'], unique=False)
    op.create_index(op.f('ix_jobpost_subscription_email_verified_at'), 'jobpost_subscription', ['email_verified_at'], unique=False)
    op.create_index(op.f('ix_jobpost_subscription_user_id'), 'jobpost_subscription', ['user_id'], unique=False)

    op.create_table('jobpost_alert',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('jobpost_subscription_id', sa.Integer(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
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
    op.alter_column('filterset', 'name', existing_type=sa.Unicode(), nullable=True)
    op.alter_column('filterset', 'title', existing_type=sa.Unicode(), nullable=True)


def downgrade():
    op.alter_column('filterset', 'name', existing_type=sa.Unicode(), nullable=False)
    op.alter_column('filterset', 'title', existing_type=sa.Unicode(), nullable=False)
    op.drop_index(op.f('ix_filterset_sitemap'), table_name='filterset')
    op.drop_column(u'filterset', 'sitemap')
    op.drop_table('jobpost_jobpost_alert')
    op.drop_index(op.f('ix_jobpost_alert_jobpost_subscription_id'), table_name='jobpost_alert')
    op.drop_table('jobpost_alert')
    op.drop_index(op.f('ix_jobpost_subscription_user_id'), table_name='jobpost_subscription')
    op.drop_index(op.f('ix_jobpost_subscription_email_verified_at'), table_name='jobpost_subscription')
    op.drop_index(op.f('ix_jobpost_subscription_anon_user_id'), table_name='jobpost_subscription')
    op.drop_index(op.f('ix_jobpost_subscription_active'), table_name='jobpost_subscription')
    op.drop_table('jobpost_subscription')
