# -*- coding: utf-8 -*-
"""jobapps

Revision ID: 95eacca1a9d
Revises: d286e09aee1
Create Date: 2013-09-12 21:06:06.501249

"""

# revision identifiers, used by Alembic.
revision = '95eacca1a9d'
down_revision = 'd286e09aee1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'job_application',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('jobpost_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.Unicode(length=80), nullable=True),
        sa.Column('phone', sa.Unicode(length=80), nullable=True),
        sa.Column('message_text', sa.UnicodeText(), nullable=True),
        sa.Column('message_html', sa.UnicodeText(), nullable=True),
        sa.Column('response', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('job_application')
