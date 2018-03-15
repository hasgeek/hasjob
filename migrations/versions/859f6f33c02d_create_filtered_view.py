"""creates filtered view

Revision ID: 859f6f33c02d
Revises: 8a37fe07ef9d
Create Date: 2018-03-15 14:09:04.609985

"""

# revision identifiers, used by Alembic.
revision = '859f6f33c02d'
down_revision = 'b26b524d3fba'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table('filtered_view',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.UnicodeText(), nullable=False),
        sa.Column('pay_currency', sa.CHAR(length=3), nullable=True),
        sa.Column('pay_cash_min', sa.Integer(), nullable=True),
        sa.Column('equity', sa.Boolean(), nullable=False),
        sa.Column('remote_location', sa.Boolean(), nullable=False),
        sa.Column('keywords', sa.UnicodeText(), nullable=False),
        sa.Column('location_names', postgresql.ARRAY(sa.Unicode(), dimensions=1), nullable=True),
        sa.Column('name', sa.Unicode(length=250), nullable=False),
        sa.Column('title', sa.Unicode(length=250), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.UniqueConstraint('name')
    )

    op.create_table('filteredview_jobcategory_table',
        sa.Column('filtered_view_id', sa.Integer(), nullable=False),
        sa.Column('jobcategory_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['filtered_view_id'], ['filtered_view.id'], ),
        sa.ForeignKeyConstraint(['jobcategory_id'], ['jobcategory.id'], ),
        sa.PrimaryKeyConstraint('filtered_view_id', 'jobcategory_id')
    )

    op.create_table('filteredview_jobtype_table',
        sa.Column('filtered_view_id', sa.Integer(), nullable=False),
        sa.Column('jobtype_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['filtered_view_id'], ['filtered_view.id'], ),
        sa.ForeignKeyConstraint(['jobtype_id'], ['jobtype.id'], ),
        sa.PrimaryKeyConstraint('filtered_view_id', 'jobtype_id')
    )

    op.create_table('filteredview_tag_table',
        sa.Column('filtered_view_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['filtered_view_id'], ['filtered_view.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ),
        sa.PrimaryKeyConstraint('filtered_view_id', 'tag_id')
    )

    op.create_table('filteredview_domain_table',
        sa.Column('filtered_view_id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['domain_id'], ['domain.id'], ),
        sa.ForeignKeyConstraint(['filtered_view_id'], ['filtered_view.id'], ),
        sa.PrimaryKeyConstraint('filtered_view_id', 'domain_id')
    )


def downgrade():
    op.drop_table('filteredview_domain_table')
    op.drop_table('filteredview_tag_table')
    op.drop_table('filteredview_jobtype_table')
    op.drop_table('filteredview_jobcategory_table')
    op.drop_table('filtered_view')
