# -*- coding: utf-8 -*-
"""Payscale info

Revision ID: 34e1d4b2f636
Revises: 472ca8e93765
Create Date: 2014-03-22 05:15:43.496558

"""

# revision identifiers, used by Alembic.
revision = '34e1d4b2f636'
down_revision = '472ca8e93765'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('jobpost', sa.Column('pay_cash_max', sa.Integer(), nullable=True))
    op.add_column('jobpost', sa.Column('pay_cash_min', sa.Integer(), nullable=True))
    op.add_column(
        'jobpost', sa.Column('pay_currency', sa.CHAR(length=3), nullable=True)
    )
    op.add_column('jobpost', sa.Column('pay_equity_max', sa.Numeric(), nullable=True))
    op.add_column('jobpost', sa.Column('pay_equity_min', sa.Numeric(), nullable=True))
    op.add_column('jobpost', sa.Column('pay_type', sa.SmallInteger(), nullable=True))


def downgrade():
    op.drop_column('jobpost', 'pay_type')
    op.drop_column('jobpost', 'pay_equity_min')
    op.drop_column('jobpost', 'pay_equity_max')
    op.drop_column('jobpost', 'pay_currency')
    op.drop_column('jobpost', 'pay_cash_min')
    op.drop_column('jobpost', 'pay_cash_max')
