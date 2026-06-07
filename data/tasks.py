import sqlalchemy
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Task(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'tasks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    info = sqlalchemy.Column(sqlalchemy.String)
    address = sqlalchemy.Column(sqlalchemy.String)
    url_pic = sqlalchemy.Column(sqlalchemy.String)
    start_date = sqlalchemy.Column(sqlalchemy.DateTime)
    end_date = sqlalchemy.Column(sqlalchemy.DateTime)
    people_count = sqlalchemy.Column(sqlalchemy.Integer)
    tags = sqlalchemy.Column(sqlalchemy.String)
    is_archived = sqlalchemy.Column(sqlalchemy.Boolean)
    user = orm.relationship('User', back_populates='tasks')
    organization = orm.relationship('Organization', back_populates='tasks')