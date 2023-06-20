from __future__ import annotations

from . import Model, backref, relationship, sa
from .jobpost import JobPost
from .reportcode import ReportCode
from .user import User

__all__ = ['JobPostReport']


# No BaseMixin here because this is a legacy class (datetime serves the purpose of created_at and updated_at)
class JobPostReport(Model):
    __tablename__ = 'jobpostreport'

    id = sa.orm.mapped_column(sa.Integer, primary_key=True)  # noqa: A003
    user_id = sa.orm.mapped_column(None, sa.ForeignKey('user.id'), nullable=True)
    user = relationship(User)
    datetime = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True), default=sa.func.utcnow(), nullable=False
    )
    post_id = sa.orm.mapped_column(
        sa.Integer, sa.ForeignKey('jobpost.id'), nullable=False
    )
    post = relationship(
        JobPost,
        primaryjoin=post_id == JobPost.id,
        backref=backref('flags', cascade='all, delete-orphan'),
    )
    reportcode_id = sa.orm.mapped_column(
        sa.Integer, sa.ForeignKey('reportcode.id'), nullable=False
    )
    reportcode = relationship(ReportCode, primaryjoin=reportcode_id == ReportCode.id)
    report_code = sa.orm.synonym('reportcode_id')

    ipaddr = sa.orm.mapped_column(sa.String(45), nullable=False)
    useragent = sa.orm.mapped_column(sa.Unicode(250), nullable=True)
