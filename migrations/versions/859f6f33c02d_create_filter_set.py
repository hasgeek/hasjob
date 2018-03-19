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
    op.create_table('filterset',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.UnicodeText(), nullable=False),
        sa.Column('pay_currency', sa.CHAR(length=3), nullable=True),
        sa.Column('pay_cash', sa.Integer(), nullable=True),
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

    op.create_index(op.f('ix_filterset_remote_location'), 'filterset', ['remote_location'], unique=False)
    op.create_index(op.f('ix_filterset_pay_currency'), 'filterset', ['pay_currency'], unique=False)
    op.create_index(op.f('ix_filterset_pay_cash'), 'filterset', ['pay_cash'], unique=False)
    op.create_index(op.f('ix_filterset_equity'), 'filterset', ['equity'], unique=False)
    op.create_index(op.f('ix_filterset_keywords'), 'filterset', ['keywords'], unique=False)

    op.execute(sa.DDL('''
        CREATE INDEX ix_filterset_location_geonameids on filterset USING gin (location_geonameids);
    '''))

    op.create_table('filterset_jobcategory_table',
        sa.Column('filterset_id', sa.Integer(), nullable=False),
        sa.Column('jobcategory_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['filterset_id'], ['filterset.id'], ),
        sa.ForeignKeyConstraint(['jobcategory_id'], ['jobcategory.id'], ),
        sa.PrimaryKeyConstraint('filterset_id', 'jobcategory_id')
    )

    op.create_table('filterset_jobtype_table',
        sa.Column('filterset_id', sa.Integer(), nullable=False),
        sa.Column('jobtype_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['filterset_id'], ['filterset.id'], ),
        sa.ForeignKeyConstraint(['jobtype_id'], ['jobtype.id'], ),
        sa.PrimaryKeyConstraint('filterset_id', 'jobtype_id')
    )

    op.create_table('filterset_tag_table',
        sa.Column('filterset_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['filterset_id'], ['filterset.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ),
        sa.PrimaryKeyConstraint('filterset_id', 'tag_id')
    )

    op.create_table('filterset_domain_table',
        sa.Column('filterset_id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['domain_id'], ['domain.id'], ),
        sa.ForeignKeyConstraint(['filterset_id'], ['filterset.id'], ),
        sa.PrimaryKeyConstraint('filterset_id', 'domain_id')
    )

    op.create_index(op.f('ix_filterset_jobcategory_table_jobcategory_id'), 'filterset_jobcategory_table', ['jobcategory_id'], unique=False)
    op.create_index(op.f('ix_filterset_jobtype_table_jobtype_id'), 'filterset_jobtype_table', ['jobtype_id'], unique=False)
    op.create_index(op.f('ix_filterset_tag_table_tag_id'), 'filterset_tag_table', ['tag_id'], unique=False)
    op.create_index(op.f('ix_filterset_domain_table_domain_id'), 'filterset_domain_table', ['domain_id'], unique=False)


def downgrade():
    op.drop_index('ix_filterset_domain_table_domain_id', 'filterset_domain_table')
    op.drop_index('ix_filterset_tag_table_tag_id', 'filterset_tag_table')
    op.drop_index('ix_filterset_jobtype_table_jobtype_id', 'filterset_jobtype_table')
    op.drop_index('ix_filterset_jobcategory_table_jobcategory_id', 'filterset_jobcategory_table')
    op.drop_table('filterset_domain_table')
    op.drop_table('filterset_tag_table')
    op.drop_table('filterset_jobtype_table')
    op.drop_table('filterset_jobcategory_table')
    op.drop_index('ix_filterset_location_geonameids', 'filterset')
    op.drop_index(op.f('ix_filterset_keywords'), table_name='filterset')
    op.drop_index(op.f('ix_filterset_equity'), table_name='filterset')
    op.drop_index(op.f('ix_filterset_pay_cash'), table_name='filterset')
    op.drop_index(op.f('ix_filterset_pay_currency'), table_name='filterset')
    op.drop_index(op.f('ix_filterset_remote_location'), table_name='filterset')
    op.drop_table('filterset')
