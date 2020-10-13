"""Add 'auto' to auto tagging tables

Revision ID: 17e2b3e7055a
Revises: c039166ecc6
Create Date: 2016-03-14 18:39:58.737572

"""

# revision identifiers, used by Alembic.
revision = '17e2b3e7055a'
down_revision = 'c039166ecc6'

from alembic import op

# import sqlalchemy as sa


def upgrade():
    op.drop_constraint('board_domain_pkey', 'board_domain', type_='primary')
    op.drop_index('ix_board_domain_domain', 'board_domain')
    op.drop_constraint('board_domain_board_id_fkey', 'board_domain', type_='foreignkey')
    op.rename_table('board_domain', 'board_auto_domain')
    op.create_primary_key(
        'board_auto_domain_pkey', 'board_auto_domain', ['board_id', 'domain']
    )
    op.create_index('ix_board_auto_domain_domain', 'board_auto_domain', ['domain'])
    op.create_foreign_key(
        'board_auto_domain_board_id_fkey',
        'board_auto_domain',
        'board',
        ['board_id'],
        ['id'],
    )

    op.drop_constraint('board_location_pkey', 'board_location', type_='primary')
    op.drop_index('ix_board_location_geonameid', 'board_location')
    op.drop_constraint(
        'board_location_board_id_fkey', 'board_location', type_='foreignkey'
    )
    op.rename_table('board_location', 'board_auto_location')
    op.create_primary_key(
        'board_auto_location_pkey', 'board_auto_location', ['board_id', 'geonameid']
    )
    op.create_index(
        'ix_board_auto_location_geonameid', 'board_auto_location', ['geonameid']
    )
    op.create_foreign_key(
        'board_auto_location_board_id_fkey',
        'board_auto_location',
        'board',
        ['board_id'],
        ['id'],
    )


def downgrade():
    op.drop_constraint(
        'board_auto_location_pkey', 'board_auto_location', type_='primary'
    )
    op.drop_index('ix_board_auto_location_geonameid', 'board_auto_location')
    op.drop_constraint(
        'board_auto_location_board_id_fkey', 'board_auto_location', type_='foreignkey'
    )
    op.rename_table('board_auto_location', 'board_location')
    op.create_primary_key(
        'board_location_pkey', 'board_location', ['board_id', 'geonameid']
    )
    op.create_index('ix_board_location_geonameid', 'board_location', ['geonameid'])
    op.create_foreign_key(
        'board_location_board_id_fkey', 'board_location', 'board', ['board_id'], ['id']
    )

    op.drop_constraint('board_auto_domain_pkey', 'board_auto_domain', type_='primary')
    op.drop_index('ix_board_auto_domain_domain', 'board_auto_domain')
    op.drop_constraint(
        'board_auto_domain_board_id_fkey', 'board_auto_domain', type_='foreignkey'
    )
    op.rename_table('board_auto_domain', 'board_domain')
    op.create_primary_key('board_domain_pkey', 'board_domain', ['board_id', 'domain'])
    op.create_index('ix_board_domain_domain', 'board_domain', ['domain'])
    op.create_foreign_key(
        'board_domain_board_id_fkey', 'board_domain', 'board', ['board_id'], ['id']
    )
