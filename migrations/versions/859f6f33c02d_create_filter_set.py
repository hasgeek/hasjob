"""creates filter set

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
    op.create_table('filter_set',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.UnicodeText(), nullable=False),
        sa.Column('pay_currency', sa.CHAR(length=3), nullable=True),
        sa.Column('pay_cash_min', sa.Integer(), nullable=True),
        sa.Column('equity', sa.Boolean(), nullable=False),
        sa.Column('remote_location', sa.Boolean(), nullable=False),
        sa.Column('keywords', sa.UnicodeText(), nullable=False),
        sa.Column('location_geonameids', postgresql.ARRAY(sa.Integer(), dimensions=1), nullable=True),
        sa.Column('name', sa.Unicode(length=250), nullable=False),
        sa.Column('title', sa.Unicode(length=250), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['board_id'], ['board.id'], ),
        sa.UniqueConstraint('name')
    )

    op.create_index(op.f('ix_filter_set_remote_location'), 'filter_set', ['remote_location'], unique=False)
    op.create_index(op.f('ix_filter_set_pay_currency'), 'filter_set', ['pay_currency'], unique=False)
    op.create_index(op.f('ix_filter_set_pay_cash_min'), 'filter_set', ['pay_cash_min'], unique=False)
    op.create_index(op.f('ix_filter_set_equity'), 'filter_set', ['equity'], unique=False)
    op.create_index(op.f('ix_filter_set_keywords'), 'filter_set', ['keywords'], unique=False)

    op.execute(sa.DDL('''
        CREATE INDEX idx_filter_set_location_geonameids on filter_set USING gin (location_geonameids);
    '''))

    op.create_table('filterset_jobcategory_table',
        sa.Column('filter_set_id', sa.Integer(), nullable=False),
        sa.Column('jobcategory_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['filter_set_id'], ['filter_set.id'], ),
        sa.ForeignKeyConstraint(['jobcategory_id'], ['jobcategory.id'], ),
        sa.PrimaryKeyConstraint('filter_set_id', 'jobcategory_id')
    )

    op.create_table('filterset_jobtype_table',
        sa.Column('filter_set_id', sa.Integer(), nullable=False),
        sa.Column('jobtype_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['filter_set_id'], ['filter_set.id'], ),
        sa.ForeignKeyConstraint(['jobtype_id'], ['jobtype.id'], ),
        sa.PrimaryKeyConstraint('filter_set_id', 'jobtype_id')
    )

    op.create_table('filterset_tag_table',
        sa.Column('filter_set_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['filter_set_id'], ['filter_set.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ),
        sa.PrimaryKeyConstraint('filter_set_id', 'tag_id')
    )

    op.create_table('filterset_domain_table',
        sa.Column('filter_set_id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['domain_id'], ['domain.id'], ),
        sa.ForeignKeyConstraint(['filter_set_id'], ['filter_set.id'], ),
        sa.PrimaryKeyConstraint('filter_set_id', 'domain_id')
    )


def downgrade():
    op.drop_table('filterset_domain_table')
    op.drop_table('filterset_tag_table')
    op.drop_table('filterset_jobtype_table')
    op.drop_table('filterset_jobcategory_table')
    op.drop_index('idx_filter_set_location_geonameids', 'filter_set')
    op.drop_index(op.f('ix_filter_set_keywords'), table_name='filter_set')
    op.drop_index(op.f('ix_filter_set_equity'), table_name='filter_set')
    op.drop_index(op.f('ix_filter_set_pay_cash_min'), table_name='filter_set')
    op.drop_index(op.f('ix_filter_set_pay_currency'), table_name='filter_set')
    op.drop_index(op.f('ix_filter_set_remote_location'), table_name='filter_set')
    op.drop_table('filter_set')
