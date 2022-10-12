from sqlalchemy import Column, Integer, DateTime, String, Enum, func, ARRAY, ForeignKey
from sqlalchemy.orm import relationship

from . import OrmBase
from ..enums import SeasonState, UserSeasonPointChangeType


class SeasonOrm(OrmBase):
    __tablename__ = 'seasons'

    id = Column(Integer, primary_key=True, autoincrement=True)

    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship('GroupOrm', foreign_keys='SeasonOrm.group_id')

    state = Column(Enum(SeasonState), nullable=False, default=SeasonState.initial)

    name = Column(String)
    code = Column(Integer)

    start_time = Column(DateTime)
    end_time = Column(DateTime)

    east_game_horse_point = Column(ARRAY(Integer, dimensions=1))
    south_game_horse_point = Column(ARRAY(Integer, dimensions=1))

    create_time = Column('create_time', DateTime, nullable=False, server_default=func.now())
    update_time = Column('update_time', DateTime)
    delete_time = Column('delete_time', DateTime)


class UserSeasonPointOrm(OrmBase):
    __tablename__ = 'user_season_points'

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)
    user = relationship('UserOrm', foreign_keys='UserSeasonPointOrm.user_id')

    season_id = Column(Integer, ForeignKey('seasons.id'), nullable=False, primary_key=True)
    season = relationship('SeasonOrm', foreign_keys='UserSeasonPointOrm.season_id')

    point = Column(Integer, nullable=False, default=0)

    last_change_log_id = Column(Integer, ForeignKey('user_season_point_change_logs.id'))
    last_change_log = relationship('UserSeasonPointChangeLogOrm',
                                   foreign_keys='UserSeasonPointOrm.last_change_log_id')


class UserSeasonPointChangeLogOrm(OrmBase):
    __tablename__ = 'user_season_point_change_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('UserOrm', foreign_keys='UserSeasonPointChangeLogOrm.user_id')

    season_id = Column(Integer, ForeignKey('seasons.id'), nullable=False)
    season = relationship('SeasonOrm', foreign_keys='UserSeasonPointChangeLogOrm.season_id')

    change_type = Column(Enum(UserSeasonPointChangeType), nullable=False)
    change_point = Column(Integer, nullable=False)

    related_game_id = Column(Integer, ForeignKey('games.id'))
    related_game = relationship('GameOrm', foreign_keys='UserSeasonPointChangeLogOrm.related_game_id')

    create_time = Column('create_time', DateTime, nullable=False, server_default=func.now())


__all__ = ("SeasonOrm", "UserSeasonPointOrm", "UserSeasonPointChangeLogOrm")
