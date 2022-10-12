from sqlalchemy import Column, String, BigInteger, Integer

from . import OrmBase


class UserOrm(OrmBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String)
    password = Column(String)
    nickname = Column(String)
    binding_qq = Column(BigInteger)


__all__ = ("UserOrm",)
