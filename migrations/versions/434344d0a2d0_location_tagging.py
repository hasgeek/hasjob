"""Location tagging

Revision ID: 434344d0a2d0
Revises: 441fd49059e3
Create Date: 2014-06-12 02:32:50.090106

"""

# revision identifiers, used by Alembic.
revision = '434344d0a2d0'
down_revision = '441fd49059e3'

from alembic import op
import sqlalchemy as sa

from coaster.sqlalchemy import JsonDict


def upgrade():
    op.create_table(
        'job_location',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('jobpost_id', sa.Integer(), nullable=False),
        sa.Column('geonameid', sa.Integer(), nullable=False),
        sa.Column('primary', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id']),
        sa.PrimaryKeyConstraint('jobpost_id', 'geonameid'),
    )
    op.add_column('jobpost', sa.Column('parsed_location', JsonDict(), nullable=True))


def downgrade():
    op.drop_column('jobpost', 'parsed_location')
    op.drop_table('job_location')
