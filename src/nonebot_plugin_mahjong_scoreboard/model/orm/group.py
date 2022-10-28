from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, BigInteger, ForeignKey, Index
from sqlalchemy.orm import relationship

from . import data_source

if TYPE_CHECKING:
    from .season import SeasonOrm


@data_source.registry.mapped
class GroupOrm:
    __tablename__ = 'groups'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    binding_qq: int = Column(BigInteger)

    running_season_id: int = Column(Integer, ForeignKey('seasons.id'))
    running_season: 'SeasonOrm' = relationship('SeasonOrm', foreign_keys='GroupOrm.running_season_id')

    prev_game_code_base: int = Column(Integer)
    prev_game_code_identifier: int = Column(Integer)

    __table_args__ = (
        Index("groups_binding_qq_idx", "binding_qq"),
    )


__all__ = ("GroupOrm",)
