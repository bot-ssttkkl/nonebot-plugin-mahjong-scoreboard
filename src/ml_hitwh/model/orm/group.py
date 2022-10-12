from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from . import OrmBase

if TYPE_CHECKING:
    from .season import SeasonOrm


class GroupOrm(OrmBase):
    __tablename__ = 'groups'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    binding_qq: int = Column(BigInteger)

    running_season_id: int = Column(Integer, ForeignKey('seasons.id'))
    running_season: 'SeasonOrm' = relationship('SeasonOrm', foreign_keys='GroupOrm.running_season_id')

    prev_game_code_base: int = Column(Integer)
    prev_game_code_identifier: int = Column(Integer)


__all__ = ("GroupOrm",)
