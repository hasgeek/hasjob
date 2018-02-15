"""Reports track users now

Revision ID: 3e27bf9706ee
Revises: 4c8265da3caa
Create Date: 2013-11-22 01:20:09.514748

"""

# revision identifiers, used by Alembic.
revision = '3e27bf9706ee'
down_revision = '4c8265da3caa'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('jobpostreport', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('jobpostreport_user_id_fkey', 'jobpostreport', 'user', ['user_id'], ['id'])


def downgrade():
    op.drop_constraint('jobpostreport_user_id_fkey', 'jobpostreport', 'foreignkey')
    op.drop_column('jobpostreport', 'user_id')
