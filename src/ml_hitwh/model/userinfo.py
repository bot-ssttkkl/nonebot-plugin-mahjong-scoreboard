from sqlalchemy import Column, String, BigInteger

from ml_hitwh.model import OrmBase


class UserInfoOrm(OrmBase):
    __tablename__ = 'userinfo'

    user_id = Column('user_id', BigInteger, primary_key=True)
    group_id = Column('group_id', BigInteger, primary_key=True)
    nickname = Column('nickname', String)
