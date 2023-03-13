from sqlalchemy import BigInteger, Index
from sqlalchemy.orm import Mapped, mapped_column

from ._data_source import data_source


@data_source.registry.mapped
class UserOrm:
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    binding_qq: Mapped[int] = mapped_column(BigInteger)

    __table_args__ = (
        Index("users_binding_qq_idx", "binding_qq"),
    )


__all__ = ("UserOrm",)
