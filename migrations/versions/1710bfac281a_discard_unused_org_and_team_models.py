"""Discard unused Org and Team models

Revision ID: 1710bfac281a
Revises: 2aab4c974a75
Create Date: 2015-03-05 16:19:18.921362

"""

# revision identifiers, used by Alembic.
revision = '1710bfac281a'
down_revision = '2aab4c974a75'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.drop_index('ix_jobpost_org_id', table_name='jobpost')
    op.drop_constraint(u'jobpost_org_id_fkey', 'jobpost', type_='foreignkey')
    op.drop_column('jobpost', 'org_id')
    op.drop_table('users_teams')
    op.drop_table('org_location')
    op.drop_table('organization')
    op.drop_table('team')


def downgrade():
    op.create_table('team',
        sa.Column('id', sa.INTEGER(), server_default=sa.text(u"nextval('team_id_seq'::regclass)"), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column('title', sa.VARCHAR(length=250), autoincrement=False, nullable=False),
        sa.Column('userid', sa.VARCHAR(length=22), autoincrement=False, nullable=False),
        sa.Column('owners', sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column('orgid', sa.VARCHAR(length=22), autoincrement=False, nullable=False),
        sa.Column('members', sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('id', name=u'team_pkey'),
        postgresql_ignore_search_path=False
        )
    op.create_table('organization',
        sa.Column('id', sa.INTEGER(), server_default=sa.text(u"nextval('organization_id_seq'::regclass)"), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column('domain', sa.VARCHAR(length=253), autoincrement=False, nullable=True),
        sa.Column('logo_image', sa.VARCHAR(length=250), autoincrement=False, nullable=True),
        sa.Column('cover_image', sa.VARCHAR(length=250), autoincrement=False, nullable=True),
        sa.Column('description', sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column('status', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('userid', sa.VARCHAR(length=22), autoincrement=False, nullable=False),
        sa.Column('name', sa.VARCHAR(length=250), autoincrement=False, nullable=False),
        sa.Column('title', sa.VARCHAR(length=250), autoincrement=False, nullable=False),
        sa.Column('admin_team_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('hiring_team_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['admin_team_id'], [u'team.id'], name=u'organization_admin_team_id_fkey', ondelete=u'SET NULL'),
        sa.ForeignKeyConstraint(['hiring_team_id'], [u'team.id'], name=u'organization_hiring_team_id_fkey', ondelete=u'SET NULL'),
        sa.PrimaryKeyConstraint('id', name=u'organization_pkey'),
        postgresql_ignore_search_path=False
        )
    op.create_table('org_location',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column('latitude', sa.NUMERIC(), autoincrement=False, nullable=True),
        sa.Column('longitude', sa.NUMERIC(), autoincrement=False, nullable=True),
        sa.Column('org_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('title', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
        sa.Column('address1', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
        sa.Column('address2', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
        sa.Column('city', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
        sa.Column('state', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
        sa.Column('postcode', sa.VARCHAR(length=16), autoincrement=False, nullable=True),
        sa.Column('country', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
        sa.Column('geonameid', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('url_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['org_id'], [u'organization.id'], name=u'org_location_org_id_fkey'),
        sa.PrimaryKeyConstraint('id', name=u'org_location_pkey')
        )
    op.create_table('users_teams',
        sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('team_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['team_id'], [u'team.id'], name=u'users_teams_team_id_fkey'),
        sa.ForeignKeyConstraint(['user_id'], [u'user.id'], name=u'users_teams_user_id_fkey'),
        sa.PrimaryKeyConstraint('user_id', 'team_id', name=u'users_teams_pkey')
        )
    op.add_column('jobpost', sa.Column('org_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(u'jobpost_org_id_fkey', 'jobpost', 'organization', ['org_id'], ['id'])
    op.create_index('ix_jobpost_org_id', 'jobpost', ['org_id'], unique=False)
