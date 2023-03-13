from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, ForeignKey, Index
from sqlalchemy.orm import mapped_column, relationship, Mapped

from ._data_source import data_source

if TYPE_CHECKING:
    from .season import SeasonOrm


@data_source.registry.mapped
class GroupOrm:
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    binding_qq: Mapped[int] = mapped_column(BigInteger)

    running_season_id: Mapped[Optional[int]] = mapped_column(ForeignKey('seasons.id'))
    running_season: Mapped[Optional['SeasonOrm']] = relationship(foreign_keys='GroupOrm.running_season_id')

    prev_game_code_base: Mapped[int]
    prev_game_code_identifier: Mapped[int]

    __table_args__ = (
        Index("groups_binding_qq_idx", "binding_qq"),
    )


__all__ = ("GroupOrm",)
