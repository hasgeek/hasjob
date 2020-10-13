"""Jobpost search

Revision ID: 2aab4c974a75
Revises: 48f145e9d55f
Create Date: 2015-03-03 14:00:27.955410

"""

# revision identifiers, used by Alembic.
revision = '2aab4c974a75'
down_revision = '48f145e9d55f'

from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'jobpost', sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True)
    )
    op.execute(
        sa.DDL(
            '''
        CREATE FUNCTION jobpost_search_vector_update() RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                NEW.search_vector = to_tsvector('english', COALESCE(NEW.company_name, '') || ' ' || COALESCE(NEW.headline, '') || ' ' || COALESCE(NEW.headlineb, '') || ' ' || COALESCE(NEW.description, '') || ' ' || COALESCE(NEW.perks, ''));
            END IF;
            IF TG_OP = 'UPDATE' THEN
                IF NEW.headline <> OLD.headline OR COALESCE(NEW.headlineb, '') <> COALESCE(OLD.headlineb, '') OR NEW.description <> OLD.description OR NEW.perks <> OLD.perks THEN
                    NEW.search_vector = to_tsvector('english', COALESCE(NEW.company_name, '') || ' ' || COALESCE(NEW.headline, '') || ' ' || COALESCE(NEW.headlineb, '') || ' ' || COALESCE(NEW.description, '') || ' ' || COALESCE(NEW.perks, ''));
                END IF;
            END IF;
            RETURN NEW;
        END
        $$ LANGUAGE 'plpgsql';

        CREATE TRIGGER jobpost_search_vector_trigger BEFORE INSERT OR UPDATE ON jobpost
        FOR EACH ROW EXECUTE PROCEDURE jobpost_search_vector_update();

        CREATE INDEX ix_jobpost_search_vector ON jobpost USING gin(search_vector);

        UPDATE jobpost SET search_vector = to_tsvector('english', COALESCE(company_name, '') || ' ' || COALESCE(headline, '') || ' ' || COALESCE(headlineb, '') || ' ' || COALESCE(description, '') || ' ' || COALESCE(perks, ''));
        '''
        )
    )


def downgrade():
    op.drop_index('ix_jobpost_search_vector', 'jobpost')
    op.execute('DROP TRIGGER jobpost_search_vector_trigger ON jobpost')
    op.execute('DROP FUNCTION jobpost_search_vector_update()')
    op.drop_column('jobpost', 'search_vector')
