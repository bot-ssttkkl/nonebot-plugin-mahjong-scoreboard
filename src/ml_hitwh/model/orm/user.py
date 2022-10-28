from sqlalchemy import Column, BigInteger, Integer, Index

from . import data_source


@data_source.registry.mapped
class UserOrm:
    __tablename__ = 'users'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    binding_qq: int = Column(BigInteger)

    __table_args__ = (
        Index("users_binding_qq_idx", "binding_qq"),
    )


__all__ = ("UserOrm",)
