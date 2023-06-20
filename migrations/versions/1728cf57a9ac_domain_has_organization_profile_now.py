"""Domain has organization profile now

Revision ID: 1728cf57a9ac
Revises: 1710bfac281a
Create Date: 2015-03-05 17:29:02.607904

"""

# revision identifiers, used by Alembic.
revision = '1728cf57a9ac'
down_revision = '1710bfac281a'

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('domain', sa.Column('title', sa.Unicode(length=250), nullable=True))
    op.add_column(
        'domain', sa.Column('legal_title', sa.Unicode(length=250), nullable=True)
    )
    op.add_column('domain', sa.Column('description', sa.UnicodeText(), nullable=True))
    op.add_column(
        'domain', sa.Column('logo_url', sa.Unicode(length=250), nullable=True)
    )
    op.add_column(
        'domain', sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True)
    )
    op.execute(
        sa.DDL(
            '''
        CREATE FUNCTION domain_search_vector_update() RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector = to_tsvector('english', COALESCE(NEW.name, '') || ' ' || COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.legal_title, '') || ' ' || COALESCE(NEW.description, ''));
            RETURN NEW;
        END
        $$ LANGUAGE 'plpgsql';

        CREATE TRIGGER domain_search_vector_trigger BEFORE INSERT OR UPDATE ON domain
        FOR EACH ROW EXECUTE PROCEDURE domain_search_vector_update();

        CREATE INDEX ix_domain_search_vector ON domain USING gin(search_vector);

        UPDATE domain SET search_vector = to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(title, '') || ' ' || COALESCE(legal_title, '') || ' ' || COALESCE(description, ''));
        '''
        )
    )


def downgrade():
    op.drop_index('ix_domain_search_vector', 'domain')
    op.execute('DROP TRIGGER domain_search_vector_trigger ON domain')
    op.execute('DROP FUNCTION domain_search_vector_update()')
    op.drop_column('domain', 'search_vector')
    op.drop_column('domain', 'logo_url')
    op.drop_column('domain', 'description')
    op.drop_column('domain', 'legal_title')
    op.drop_column('domain', 'title')
