"""Questions and answers

Revision ID: 58b342b013ba
Revises: 2aab4c974a75
Create Date: 2015-02-24 23:13:10.656412

"""

# revision identifiers, used by Alembic.
revision = '58b342b013ba'
down_revision = '2aab4c974a75'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('question',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('jobpost_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Unicode(length=250), nullable=False),
        sa.Column('status', sa.SmallInteger(), nullable=False),
        sa.Column('dupe_of_id', sa.Integer(), nullable=True),
        sa.Column('dupe_marked_by_id', sa.Integer(), nullable=True),
        sa.Column('dupe_marked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dupe_marked_by_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['dupe_of_id'], ['question.id'], ),
        sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
    op.create_index(op.f('ix_question_jobpost_id'), 'question', ['jobpost_id'], unique=False)
    op.create_index(op.f('ix_question_user_id'), 'question', ['user_id'], unique=False)
    op.create_table('question_follower',
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['question.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('question_id', 'user_id')
        )
    op.create_index(op.f('ix_question_follower_user_id'), 'question_follower', ['user_id'], unique=False)
    op.create_table('answer',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.UnicodeText(), nullable=False),
        sa.Column('relevance', sa.SmallInteger(), nullable=False),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('edited_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['edited_by_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['question.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('question_id', 'user_id')
        )
    op.create_index(op.f('ix_answer_user_id'), 'answer', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_answer_user_id'), table_name='answer')
    op.drop_table('answer')
    op.drop_index(op.f('ix_question_follower_user_id'), table_name='question_follower')
    op.drop_table('question_follower')
    op.drop_index(op.f('ix_question_user_id'), table_name='question')
    op.drop_index(op.f('ix_question_jobpost_id'), table_name='question')
    op.drop_table('question')
