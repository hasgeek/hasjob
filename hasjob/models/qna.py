# -*- coding: utf-8 -*-

from datetime import datetime
from coaster.utils import LabeledEnum
from baseframe import __
from . import db, TimestampMixin, BaseMixin
from .user import User
from .jobpost import JobPost


class QUESTION_STATUS(LabeledEnum):
    PUBLIC = (1, __("Public"))        # Asker posted a question
    WITHDRAWN = (2, __("Withdrawn"))  # Asker withdrew the question
    DECLINED = (3, __("Declined"))    # Employer declined to answer
    REMOVED = (4, __("Removed"))      # Moderator removed the question


#: Larger number = more relevant. Insert new values where applicable
class ANSWER_RELEVANCE(LabeledEnum):
    COMMUNITY = (10, 'community', __("From the community"))
    MODERATOR = (20, 'moderator', __("From a moderator"))
    ORG = (30, 'org', __("From someone at the organization"))
    EMPLOYER = (40, 'employer', __("From the employer"))


question_follower_table = db.Table('question_follower', db.Model.metadata,
    db.Column('question_id', None, db.ForeignKey('question.id'), primary_key=True),
    db.Column('user_id', None, db.ForeignKey('user.id'), primary_key=True, index=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
    )


# Question uses BaseMixin instead of BaseScopedIdMixin or Base*NameMixin because questions could
# be attached to other kinds of entities in future and the parent-based constraints will be a problem.
class Question(BaseMixin, db.Model):
    __tablename__ = 'question'
    #: Job this question is for
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'), nullable=False, index=True)
    jobpost = db.relationship(JobPost, backref=db.backref('questions', cascade='all, delete-orphan'))

    #: User who asked
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False, index=True)
    user = db.relationship(User, foreign_keys=[user_id], backref='questions')

    #: The question
    title = db.Column(db.Unicode(250), nullable=False)
    #: Question status
    status = db.Column(db.SmallInteger, nullable=False, default=QUESTION_STATUS.PUBLIC)

    #: This question is a dupe of another question
    dupe_of_id = db.Column(None, db.ForeignKey('question.id'), nullable=True)
    dupe_of = db.relationship('Question', backref=db.backref('dupes', remote_side='Question.id'))

    #: This user marked it as a dupe
    dupe_marked_by_id = db.Column(None, db.ForeignKey('user.id'), nullable=True)
    dupe_marked_by = db.relationship(User, foreign_keys=[dupe_marked_by_id])
    #: This is when it was marked as a dupe
    dupe_marked_at = db.Column(db.DateTime, nullable=True)

    #: Users who want to be notified of answers
    followers = db.relationship(User, secondary=question_follower_table, lazy='dynamic',
        backref='followed_questions')

    @property
    def status_label(self):
        return QUESTION_STATUS[self.status]

    @property
    def is_public(self):
        return self.status == QUESTION_STATUS.PUBLIC

    def visible_to(self, user):
        if self.status == QUESTION_STATUS.PUBLIC:
            return True
        elif user is not None and self.status == QUESTION_STATUS.DECLINED:
            if user == self.user or self.jobpost.admin_is(user):
                return True
        return False

    def make_dupe_of(self, question, user):
        if question.jobpost != self.jobpost:
            raise ValueError("Can't dupe with a question from another jobpost")
        self.dupe_of = question
        self.duped_by = user
        self.duped_at = datetime.utcnow()

    @classmethod
    def migrate_user(cls, user, other_user):
        db.session.execute(cls.__table__.update().where(cls.user_id == user.id).values(
            user_id=other_user.id))
        db.session.execute(cls.__table__.update().where(cls.dupe_marked_by_id == user.id).values(
            dupe_marked_by_id=other_user.id))

        ufids = set([r.id for r in db.session.query(question_follower_table.c.user_id).filter(
            question_follower_table.c.user_id == user.id)])
        ofids = set([r.id for r in db.session.query(question_follower_table.c.user_id).filter(
            question_follower_table.c.user_id == other_user.id)])

        discard = ufids.intersection(ofids)  # The other user is already a follower
        migrate = ufids.difference(ofids)    # The user needs to be switched to the other user

        db.session.execute(question_follower_table.update().where(
            question_follower_table.c.user_id.in_(migrate)).values(user_id=other_user.id))
        db.session.execute(question_follower_table.delete().where(
            question_follower_table.c.user_id.in_(discard)))

        return [cls.__tablename__, question_follower_table.name]


def questions_for(jobpost, user, all=False):
    return [q for q in jobpost.questions if all or (not q.dupe_of and q.visible_to(user))]


JobPost.questions_for = questions_for


class Answer(TimestampMixin, db.Model):
    __tablename__ = 'answer'
    #: The question this is an answer to
    question_id = db.Column(None, db.ForeignKey('question.id'), nullable=False, primary_key=True)
    question = db.relationship(Question, backref='answers')
    #: The user who answered
    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False, primary_key=True, index=True)
    user = db.relationship(User, foreign_keys=[user_id], backref='answers')

    #: The answer
    description = db.Column(db.UnicodeText, nullable=False)
    #: Answer relevance
    relevance = db.Column(db.SmallInteger, nullable=False, default=ANSWER_RELEVANCE.COMMUNITY)

    edited_at = db.Column(db.DateTime, nullable=True)
    edited_by_id = db.Column(None, db.ForeignKey('user.id'), nullable=True)
    edited_by = db.relationship(User, foreign_keys=[edited_by_id])

    @property
    def relevance_label(self):
        return ANSWER_RELEVANCE[self.relevance]

    @classmethod
    def migrate_user(cls, user, other_user):
        # Edited_by_id is easy to migrate because there's no constraint
        db.session.execute(cls.__table__.update().where(cls.edited_by_id == user.id).values(edited_by_id=other_user.id))
        # User_id is harder because of the primary key constraint
        uanswers = {a.question_id: a for a in cls.query.filter_by(user=user)}
        oanswers = {a.question_id: a for a in cls.query.filter_by(user=other_user)}
        for qid in uanswers:
            if qid not in oanswers:
                # Only one user answered this question. Swap user
                uanswers[qid].user = other_user
            else:
                # Both users have answered this. Merge their answers
                ua = uanswers[qid]
                oa = oanswers[qid]
                oa.description = oa.description + ua.description
                oa.relevance = max(oa.relevance, ua.relevance)
                if ua.edited_at:
                    if not (oa.edited_at and oa.edited_at > ua.edited_at):
                        oa.edited_at = ua.edited_at
                        oa.edited_by = ua.edited_by
                db.session.delete(uanswers[qid])

        return [cls.__tablename__]
