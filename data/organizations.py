import sqlalchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy.ext.mutable import MutableList


class Organization(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'organizations'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    adress = sqlalchemy.Column(sqlalchemy.String)
    info = sqlalchemy.Column(sqlalchemy.String)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    phone_number = sqlalchemy.Column(sqlalchemy.String)
    current_tasks = sqlalchemy.Column(MutableList.as_mutable(sqlalchemy.JSON), default=[])
    archived_posts = sqlalchemy.Column(MutableList.as_mutable(sqlalchemy.JSON), default=[])

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)