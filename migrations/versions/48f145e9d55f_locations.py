"""Locations

Revision ID: 48f145e9d55f
Revises: 17a5476c8701
Create Date: 2015-02-25 14:32:12.408606

"""

# revision identifiers, used by Alembic.
revision = '48f145e9d55f'
down_revision = '17a5476c8701'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'location',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('name', sa.Unicode(length=250), nullable=False),
        sa.Column('title', sa.Unicode(length=250), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('description', sa.UnicodeText(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )


def downgrade():
    op.drop_table('location')
