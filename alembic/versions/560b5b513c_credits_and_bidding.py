"""Credits and bidding

Revision ID: 560b5b513c
Revises: 525b125ec799
Create Date: 2015-09-30 16:58:39.874408

"""

# revision identifiers, used by Alembic.
revision = '560b5b513c'
down_revision = '525b125ec799'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('bid',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('bid_type', sa.SmallInteger(), nullable=False),
        sa.Column('name', sa.Unicode(length=22), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('jobpost_id', sa.Integer(), nullable=False),
        sa.Column('start_at', sa.DateTime(), nullable=False),
        sa.Column('end_at', sa.DateTime(), nullable=False),
        sa.Column('public', sa.Boolean(), nullable=False),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('balance', sa.Integer(), nullable=False),
        sa.Column('geotargeted', sa.Boolean(), nullable=False),
        sa.CheckConstraint('end_at > start_at', name='bid_start_at_end_at'),
        sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.UniqueConstraint('name'),
        sa.PrimaryKeyConstraint('id')
        )
    op.create_index(op.f('ix_bid_end_at'), 'bid', ['end_at'], unique=False)
    op.create_index(op.f('ix_bid_start_at'), 'bid', ['start_at'], unique=False)

    op.create_table('anon_bid_impression',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('bid_id', sa.Integer(), nullable=False),
        sa.Column('anon_user_id', sa.Integer(), nullable=False),
        sa.Column('session_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['anon_user_id'], ['anon_user.id'], ),
        sa.ForeignKeyConstraint(['bid_id'], ['bid.id'], ),
        sa.PrimaryKeyConstraint('bid_id', 'anon_user_id')
        )
    op.create_index(op.f('ix_anon_bid_impression_anon_user_id'), 'anon_bid_impression', ['anon_user_id'], unique=False)

    op.create_table('bid_event_session',
        sa.Column('bid_id', sa.Integer(), nullable=False),
        sa.Column('event_session_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['bid_id'], ['bid.id'], ),
        sa.ForeignKeyConstraint(['event_session_id'], ['event_session.id'], ),
        sa.PrimaryKeyConstraint('bid_id', 'event_session_id')
        )
    op.create_index(op.f('ix_bid_event_session_event_session_id'), 'bid_event_session', ['event_session_id'], unique=False)

    op.create_table('bid_location',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('bid_id', sa.Integer(), nullable=False),
        sa.Column('geonameid', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['bid_id'], ['bid.id'], ),
        sa.PrimaryKeyConstraint('bid_id', 'geonameid')
        )
    op.create_index(op.f('ix_bid_location_geonameid'), 'bid_location', ['geonameid'], unique=False)

    op.create_table('credit_transaction',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('datetime', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('granted_by_id', sa.Integer(), nullable=True),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('memo', sa.Unicode(length=250), nullable=False),
        sa.Column('bid_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['bid_id'], ['bid.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['granted_by_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_table('user_bid_impression',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('bid_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['bid_id'], ['bid.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('bid_id', 'user_id')
        )

    op.create_index(op.f('ix_user_bid_impression_user_id'), 'user_bid_impression', ['user_id'], unique=False)
    op.add_column('job_impression', sa.Column('bid_id', sa.Integer(), nullable=True))
    op.add_column('job_impression', sa.Column('not_anon', sa.Boolean(), nullable=True))
    op.create_foreign_key('job_impression_bid_id_fkey', 'job_impression', 'bid', ['bid_id'], ['id'])


def downgrade():
    op.drop_constraint('job_impression_bid_id_fkey', 'job_impression', type_='foreignkey')
    op.drop_column('job_impression', 'not_anon')
    op.drop_column('job_impression', 'bid_id')
    op.drop_index(op.f('ix_user_bid_impression_user_id'), table_name='user_bid_impression')
    op.drop_table('user_bid_impression')
    op.drop_table('credit_transaction')
    op.drop_index(op.f('ix_bid_location_geonameid'), table_name='bid_location')
    op.drop_table('bid_location')
    op.drop_index(op.f('ix_bid_event_session_event_session_id'), table_name='bid_event_session')
    op.drop_table('bid_event_session')
    op.drop_index(op.f('ix_anon_bid_impression_anon_user_id'), table_name='anon_bid_impression')
    op.drop_table('anon_bid_impression')
    op.drop_index(op.f('ix_bid_start_at'), table_name='bid')
    op.drop_index(op.f('ix_bid_end_at'), table_name='bid')
    op.drop_table('bid')
