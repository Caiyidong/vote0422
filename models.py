from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    polls = db.relationship('Poll', backref='creator', lazy=True, foreign_keys='Poll.creator_id')
    vote_records = db.relationship('VoteRecord', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


class Poll(db.Model):
    __tablename__ = 'polls'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vote_type = db.Column(db.SmallInteger, default=1)   # 1=单选 2=多选
    max_choices = db.Column(db.Integer, default=1)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)     # None = 永不截止
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    options = db.relationship('Option', backref='poll', lazy=True, cascade='all, delete-orphan')
    vote_records = db.relationship('VoteRecord', backref='poll', lazy=True, cascade='all, delete-orphan')

    @property
    def is_expired(self):
        return self.end_time is not None and self.end_time < datetime.utcnow()

    @property
    def total_votes(self):
        return sum(o.vote_count for o in self.options)

    def __repr__(self):
        return f'<Poll {self.title}>'


class Option(db.Model):
    __tablename__ = 'options'

    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    vote_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Option {self.content}>'


class VoteRecord(db.Model):
    __tablename__ = 'vote_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('options.id'), nullable=False)
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 联合唯一约束：同一用户对同一投票只能投一次
    __table_args__ = (
        db.UniqueConstraint('user_id', 'poll_id', name='uq_user_poll'),
    )

    def __repr__(self):
        return f'<VoteRecord user={self.user_id} poll={self.poll_id}>'


class AdminLog(db.Model):
    __tablename__ = 'admin_logs'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
