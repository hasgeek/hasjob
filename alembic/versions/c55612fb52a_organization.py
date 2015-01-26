"""Organization

Revision ID: c55612fb52a
Revises: 1fce9db567a5
Create Date: 2015-01-27 02:02:42.510116

"""

# revision identifiers, used by Alembic.
revision = 'c55612fb52a'
down_revision = '1fce9db567a5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('organization',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('domain', sa.Unicode(length=253), nullable=True),
        sa.Column('logo_image', sa.Unicode(length=250), nullable=True),
        sa.Column('cover_image', sa.Unicode(length=250), nullable=True),
        sa.Column('description', sa.UnicodeText(), nullable=False),
        sa.Column('status', sa.Integer(), nullable=False),
        sa.Column('userid', sa.Unicode(length=22), nullable=False),
        sa.Column('name', sa.Unicode(length=250), nullable=False),
        sa.Column('title', sa.Unicode(length=250), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('userid')
        )
    op.create_index(op.f('ix_organization_domain'), 'organization', ['domain'], unique=False)
    op.create_table('org_location',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('latitude', sa.Numeric(), nullable=True),
        sa.Column('longitude', sa.Numeric(), nullable=True),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Unicode(length=80), nullable=True),
        sa.Column('address1', sa.Unicode(length=80), nullable=True),
        sa.Column('address2', sa.Unicode(length=80), nullable=True),
        sa.Column('city', sa.Unicode(length=80), nullable=True),
        sa.Column('state', sa.Unicode(length=80), nullable=True),
        sa.Column('postcode', sa.Unicode(length=16), nullable=True),
        sa.Column('country', sa.Unicode(length=80), nullable=True),
        sa.Column('geonameid', sa.Integer(), nullable=True),
        sa.Column('url_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'url_id')
        )
    op.create_index(op.f('ix_org_location_geonameid'), 'org_location', ['geonameid'], unique=False)
    op.add_column('jobpost', sa.Column('org_id', sa.Integer(), nullable=True))
    op.create_foreign_key('jobpost_org_id_fkey', 'jobpost', 'organization', ['org_id'], ['id'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint('jobpost_org_id_fkey', 'jobpost', type_='foreignkey')
    op.drop_column('jobpost', 'org_id')
    op.drop_index(op.f('ix_org_location_geonameid'), table_name='org_location')
    op.drop_table('org_location')
    op.drop_index(op.f('ix_organization_domain'), table_name='organization')
    op.drop_table('organization')
