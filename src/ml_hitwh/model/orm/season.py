from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Integer, DateTime, String, Enum, func, ARRAY, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from . import OrmBase
from ..enums import SeasonState, SeasonUserPointChangeType

if TYPE_CHECKING:
    from .game import GameOrm
    from .group import GroupOrm
    from .user import UserOrm


class SeasonOrm(OrmBase):
    __tablename__ = 'seasons'

    id: int = Column(Integer, primary_key=True, autoincrement=True)

    group_id: int = Column(Integer, ForeignKey('groups.id'), nullable=False)
    group: 'GroupOrm' = relationship('GroupOrm', foreign_keys='SeasonOrm.group_id')

    state: SeasonState = Column(Enum(SeasonState), nullable=False, default=SeasonState.initial)

    name: str = Column(String)
    code: int = Column(Integer)

    start_time: datetime = Column(DateTime)
    end_time: datetime = Column(DateTime)

    east_game_horse_point: List[int] = Column(ARRAY(Integer, dimensions=1))
    south_game_horse_point: List[int] = Column(ARRAY(Integer, dimensions=1))

    accessible: bool = Column(Boolean, nullable=False, default=True)
    create_time: datetime = Column('create_time', DateTime, nullable=False, server_default=func.now())
    update_time: datetime = Column('update_time', DateTime)
    delete_time: datetime = Column('delete_time', DateTime)


class SeasonUserPointOrm(OrmBase):
    __tablename__ = 'season_user_points'

    user_id: int = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)
    user: 'UserOrm' = relationship('UserOrm', foreign_keys='SeasonUserPointOrm.user_id')

    season_id: int = Column(Integer, ForeignKey('seasons.id'), nullable=False, primary_key=True)
    season: 'SeasonOrm' = relationship('SeasonOrm', foreign_keys='SeasonUserPointOrm.season_id')

    point: int = Column(Integer, nullable=False, default=0)

    last_change_log_id: int = Column(Integer, ForeignKey('season_user_point_change_logs.id'))
    last_change_log: 'SeasonUserPointChangeLogOrm' = relationship('SeasonUserPointChangeLogOrm',
                                                                  foreign_keys='SeasonUserPointOrm.last_change_log_id')


class SeasonUserPointChangeLogOrm(OrmBase):
    __tablename__ = 'season_user_point_change_logs'

    id: int = Column(Integer, primary_key=True, autoincrement=True)

    user_id: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    user: 'UserOrm' = relationship('UserOrm', foreign_keys='SeasonUserPointChangeLogOrm.user_id')

    season_id: int = Column(Integer, ForeignKey('seasons.id'), nullable=False)
    season: 'SeasonOrm' = relationship('SeasonOrm', foreign_keys='SeasonUserPointChangeLogOrm.season_id')

    change_type: SeasonUserPointChangeType = Column(Enum(SeasonUserPointChangeType), nullable=False)
    change_point: int = Column(Integer, nullable=False)

    related_game_id: int = Column(Integer, ForeignKey('games.id'))
    related_game: 'GameOrm' = relationship('GameOrm', foreign_keys='SeasonUserPointChangeLogOrm.related_game_id')

    create_time: datetime = Column('create_time', DateTime, nullable=False, server_default=func.now())


__all__ = ("SeasonOrm", "SeasonUserPointOrm", "SeasonUserPointChangeLogOrm")
