import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class UserTask(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'user_task'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id= sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    task_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('tasks.id'))
    user = orm.relationship("User", back_populates="user_tasks")
    task = orm.relationship("Task", back_populates="user_tasks")