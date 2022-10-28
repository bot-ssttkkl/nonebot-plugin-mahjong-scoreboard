from sqlalchemy import Column, String, BigInteger, Integer

from . import data_source


@data_source.registry.mapped
class UserOrm:
    __tablename__ = 'users'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    username: str = Column(String)
    password: str = Column(String)
    nickname: str = Column(String)
    binding_qq: int = Column(BigInteger)


__all__ = ("UserOrm",)
