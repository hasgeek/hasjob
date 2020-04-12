# -*- coding: utf-8 -*-
"""Campaign targeting

Revision ID: 33a61e082fb
Revises: 4616e70f18f4
Create Date: 2015-01-31 04:09:01.155311

"""

# revision identifiers, used by Alembic.
revision = '33a61e082fb'
down_revision = '4616e70f18f4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'campaign',
        sa.Column(
            'flag_has_jobapplication_response_alltime', sa.Boolean(), nullable=True
        ),
    )
    op.add_column(
        'campaign',
        sa.Column('flag_has_jobapplication_response_day', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign',
        sa.Column(
            'flag_has_jobapplication_response_month', sa.Boolean(), nullable=True
        ),
    )
    op.add_column(
        'campaign',
        sa.Column('flag_has_jobapplication_response_past', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign',
        sa.Column('flag_has_jobpost_unconfirmed_alltime', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign',
        sa.Column('flag_has_jobpost_unconfirmed_day', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign',
        sa.Column('flag_has_jobpost_unconfirmed_month', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign',
        sa.Column('flag_has_responded_candidate_alltime', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign',
        sa.Column('flag_has_responded_candidate_day', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign',
        sa.Column('flag_has_responded_candidate_month', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign',
        sa.Column('flag_has_responded_candidate_past', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign', sa.Column('flag_is_candidate_alltime', sa.Boolean(), nullable=True)
    )
    op.add_column(
        'campaign', sa.Column('flag_is_candidate_day', sa.Boolean(), nullable=True)
    )
    op.add_column(
        'campaign', sa.Column('flag_is_candidate_month', sa.Boolean(), nullable=True)
    )
    op.add_column(
        'campaign', sa.Column('flag_is_candidate_past', sa.Boolean(), nullable=True)
    )
    op.add_column(
        'campaign', sa.Column('flag_is_employer_alltime', sa.Boolean(), nullable=True)
    )
    op.add_column(
        'campaign', sa.Column('flag_is_employer_day', sa.Boolean(), nullable=True)
    )
    op.add_column(
        'campaign', sa.Column('flag_is_employer_month', sa.Boolean(), nullable=True)
    )
    op.add_column(
        'campaign', sa.Column('flag_is_employer_past', sa.Boolean(), nullable=True)
    )
    op.add_column(
        'campaign', sa.Column('flag_is_inactive_since_day', sa.Boolean(), nullable=True)
    )
    op.add_column(
        'campaign',
        sa.Column('flag_is_inactive_since_month', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign',
        sa.Column('flag_is_lurker_since_alltime', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign', sa.Column('flag_is_lurker_since_past', sa.Boolean(), nullable=True)
    )
    op.add_column(
        'campaign',
        sa.Column('flag_is_new_lurker_within_day', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign',
        sa.Column('flag_is_new_lurker_within_month', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'campaign', sa.Column('flag_is_new_since_day', sa.Boolean(), nullable=True)
    )
    op.add_column(
        'campaign', sa.Column('flag_is_new_since_month', sa.Boolean(), nullable=True)
    )
    op.add_column('campaign', sa.Column('flag_is_not_new', sa.Boolean(), nullable=True))

    op.create_index(op.f('ix_campaign_end_at'), 'campaign', ['end_at'], unique=False)
    op.create_index(
        op.f('ix_campaign_start_at'), 'campaign', ['start_at'], unique=False
    )
    op.create_index(
        op.f('ix_campaign_view_user_id'), 'campaign_view', ['user_id'], unique=False
    )


def downgrade():
    op.drop_index(op.f('ix_campaign_view_user_id'), table_name='campaign_view')
    op.drop_index(op.f('ix_campaign_start_at'), table_name='campaign')
    op.drop_index(op.f('ix_campaign_end_at'), table_name='campaign')

    op.drop_column('campaign', 'flag_is_not_new')
    op.drop_column('campaign', 'flag_is_new_since_month')
    op.drop_column('campaign', 'flag_is_new_since_day')
    op.drop_column('campaign', 'flag_is_new_lurker_within_month')
    op.drop_column('campaign', 'flag_is_new_lurker_within_day')
    op.drop_column('campaign', 'flag_is_lurker_since_past')
    op.drop_column('campaign', 'flag_is_lurker_since_alltime')
    op.drop_column('campaign', 'flag_is_inactive_since_month')
    op.drop_column('campaign', 'flag_is_inactive_since_day')
    op.drop_column('campaign', 'flag_is_employer_past')
    op.drop_column('campaign', 'flag_is_employer_month')
    op.drop_column('campaign', 'flag_is_employer_day')
    op.drop_column('campaign', 'flag_is_employer_alltime')
    op.drop_column('campaign', 'flag_is_candidate_past')
    op.drop_column('campaign', 'flag_is_candidate_month')
    op.drop_column('campaign', 'flag_is_candidate_day')
    op.drop_column('campaign', 'flag_is_candidate_alltime')
    op.drop_column('campaign', 'flag_has_responded_candidate_past')
    op.drop_column('campaign', 'flag_has_responded_candidate_month')
    op.drop_column('campaign', 'flag_has_responded_candidate_day')
    op.drop_column('campaign', 'flag_has_responded_candidate_alltime')
    op.drop_column('campaign', 'flag_has_jobpost_unconfirmed_month')
    op.drop_column('campaign', 'flag_has_jobpost_unconfirmed_day')
    op.drop_column('campaign', 'flag_has_jobpost_unconfirmed_alltime')
    op.drop_column('campaign', 'flag_has_jobapplication_response_past')
    op.drop_column('campaign', 'flag_has_jobapplication_response_month')
    op.drop_column('campaign', 'flag_has_jobapplication_response_day')
    op.drop_column('campaign', 'flag_has_jobapplication_response_alltime')
