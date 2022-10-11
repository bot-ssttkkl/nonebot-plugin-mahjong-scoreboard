from sqlalchemy import Column, Integer, BigInteger
from sqlalchemy.orm import relationship

from . import OrmBase


class GroupOrm(OrmBase):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    binding_qq = Column(BigInteger)

    running_season_id = Column(Integer)
    running_season = relationship('SeasonOrm', foreign_keys='GroupOrm.running_season_id')

    prev_game_code_base = Column(Integer)
    prev_game_code_identifier = Column(Integer)
