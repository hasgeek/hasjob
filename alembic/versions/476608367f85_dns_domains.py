"""DNS Domains

Revision ID: 476608367f85
Revises: 140e56666d9e
Create Date: 2015-02-22 13:49:44.530434

"""

# revision identifiers, used by Alembic.
revision = '476608367f85'
down_revision = '140e56666d9e'

from alembic import op
import sqlalchemy as sa
from baseframe.staticdata import webmail_domains


jobpost = sa.sql.table('jobpost',
    sa.sql.column('email_domain', sa.Unicode),
    sa.sql.column('domain_id', sa.Integer))

domain = sa.sql.table('domain',
    sa.sql.column('id', sa.Integer),
    sa.sql.column('name', sa.Unicode))


def upgrade():
    op.create_table('domain',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.Unicode(length=80), nullable=False),
        sa.Column('is_webmail', sa.Boolean(), nullable=False),
        sa.Column('is_banned', sa.Boolean(), nullable=False),
        sa.Column('banned_by_id', sa.Integer(), nullable=True),
        sa.Column('banned_reason', sa.Unicode(length=250), nullable=True),
        sa.ForeignKeyConstraint(['banned_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
        )
    op.add_column(u'jobpost', sa.Column('domain_id', sa.Integer(), nullable=True))
    op.create_foreign_key('jobpost_domain_id_fkey', 'jobpost', 'domain', ['domain_id'], ['id'])
    op.execute(sa.text(
        '''INSERT INTO domain (created_at, updated_at, name, is_webmail, is_banned)
            SELECT now() AT TIME ZONE 'UTC', now() AT TIME ZONE 'UTC', LOWER(email_domain), false, false
            FROM jobpost GROUP BY LOWER(email_domain)'''))
    # This is a risky cast from a Python set to a SQL list. Only guaranteed to work with Python 2.x
    op.execute(sa.text('''UPDATE domain SET is_webmail=true WHERE name IN %r''' %
        (tuple([str(d.lower()) for d in webmail_domains]),)))
    op.execute(sa.text(
        '''UPDATE jobpost SET domain_id = domain.id FROM domain WHERE domain.name = LOWER(jobpost.email_domain)'''))
    op.alter_column('jobpost', 'domain_id', nullable=False)


def downgrade():
    op.drop_constraint('jobpost_domain_id_fkey', 'jobpost', type_='foreignkey')
    op.drop_column(u'jobpost', 'domain_id')
    op.drop_table('domain')
