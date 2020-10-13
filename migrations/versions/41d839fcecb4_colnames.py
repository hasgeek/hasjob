"""jobapps

Revision ID: 41d839fcecb4
Revises: 1bcc4e025b04
Create Date: 2013-09-12 19:53:07.423190

"""

# revision identifiers, used by Alembic.
revision = '41d839fcecb4'
down_revision = '1bcc4e025b04'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'jobcategory',
        sa.Column(
            'created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.add_column(
        'jobcategory',
        sa.Column(
            'updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.alter_column('jobcategory', 'slug', new_column_name='name')

    op.add_column(
        'jobtype',
        sa.Column(
            'created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.add_column(
        'jobtype',
        sa.Column(
            'updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.alter_column('jobtype', 'slug', new_column_name='name')

    op.add_column(
        'reportcode',
        sa.Column(
            'created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.add_column(
        'reportcode',
        sa.Column(
            'updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.alter_column('reportcode', 'slug', new_column_name='name')

    op.alter_column('jobpost', 'created_datetime', new_column_name='created_at')
    op.add_column(
        'jobpost',
        sa.Column(
            'updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.add_column(
        'jobpost',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
    )
    op.drop_column('jobpost', 'reviewer')


def downgrade():
    op.add_column('jobpost', sa.Column('reviewer', sa.INTEGER(), nullable=True))
    op.drop_column('jobpost', 'user_id')
    op.drop_column('jobpost', 'updated_at')
    op.alter_column('jobpost', 'created_at', new_column_name='created_datetime')

    op.alter_column('reportcode', 'name', new_column_name='slug')
    op.drop_column('reportcode', 'updated_at')
    op.drop_column('reportcode', 'created_at')

    op.alter_column('jobtype', 'name', new_column_name='slug')
    op.drop_column('jobtype', 'updated_at')
    op.drop_column('jobtype', 'created_at')

    op.alter_column('jobcategory', 'name', new_column_name='slug')
    op.drop_column('jobcategory', 'updated_at')
    op.drop_column('jobcategory', 'created_at')
