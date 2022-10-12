from sqlalchemy import Column, Integer, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from . import OrmBase


class GroupOrm(OrmBase):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    binding_qq = Column(BigInteger)

    running_season_id = Column(Integer, ForeignKey('seasons.id'))
    running_season = relationship('SeasonOrm', foreign_keys='GroupOrm.running_season_id')

    prev_game_code_base = Column(Integer)
    prev_game_code_identifier = Column(Integer)


__all__ = ("GroupOrm",)
