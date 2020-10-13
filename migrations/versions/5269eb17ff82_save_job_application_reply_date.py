"""Save job application reply date

Revision ID: 5269eb17ff82
Revises: 241feed6748b
Create Date: 2015-01-31 01:46:02.016467

"""

# revision identifiers, used by Alembic.
revision = '5269eb17ff82'
down_revision = '241feed6748b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'job_application', sa.Column('replied_at', sa.DateTime(), nullable=True)
    )
    # Response status 3 = replied, 6 = rejected
    op.execute(
        sa.text(
            "UPDATE job_application SET replied_at = updated_at WHERE response IN (3, 6);"
        )
    )


def downgrade():
    op.drop_column('job_application', 'replied_at')
