"""NLP tagging

Revision ID: 1fce9db567a5
Revises: c2a626c5618
Create Date: 2015-01-20 15:08:26.942190

"""

# revision identifiers, used by Alembic.
revision = '1fce9db567a5'
down_revision = 'c2a626c5618'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('tag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('public', sa.Boolean(), nullable=False),
        sa.Column('name', sa.Unicode(length=80), nullable=False),
        sa.Column('title', sa.Unicode(length=80), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
        )
    op.create_table('jobpost_tag',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('jobpost_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ),
        sa.PrimaryKeyConstraint('jobpost_id', 'tag_id')
        )
    op.create_index(op.f('ix_jobpost_tag_tag_id'), 'jobpost_tag', ['tag_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_jobpost_tag_tag_id'), table_name='jobpost_tag')
    op.drop_table('jobpost_tag')
    op.drop_table('tag')
