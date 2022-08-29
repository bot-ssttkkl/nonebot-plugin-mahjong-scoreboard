from sqlalchemy import Column, Integer, ForeignKey, BigInteger
from sqlalchemy.orm import relationship

from ml_hitwh.model import OrmBase


class GroupInfoOrm(OrmBase):
    __tablename__ = 'groupinfo'

    group_id = Column('group_id', BigInteger, primary_key=True)

    running_season_id = Column('running_season_id', Integer, ForeignKey("season.id"))
    running_season = relationship('SeasonOrm', foreign_keys='GroupInfoOrm.running_season_id')
