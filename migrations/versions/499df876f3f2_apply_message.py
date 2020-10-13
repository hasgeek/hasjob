"""apply_message

Revision ID: 499df876f3f2
Revises: 465e724941d3
Create Date: 2013-09-12 23:44:30.028135

"""

# revision identifiers, used by Alembic.
revision = '499df876f3f2'
down_revision = '465e724941d3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('job_application', 'message_html', new_column_name='message')
    op.drop_column('job_application', 'message_text')
    op.alter_column(
        'job_application', 'email', existing_type=sa.VARCHAR(length=80), nullable=False
    )
    op.alter_column(
        'job_application', 'phone', existing_type=sa.VARCHAR(length=80), nullable=False
    )


def downgrade():
    op.alter_column(
        'job_application', 'phone', existing_type=sa.VARCHAR(length=80), nullable=True
    )
    op.alter_column(
        'job_application', 'email', existing_type=sa.VARCHAR(length=80), nullable=True
    )
    op.alter_column('job_application', 'message', new_column_name='message_html')
    op.add_column(
        'job_application', sa.Column('message_text', sa.TEXT(), nullable=True)
    )
