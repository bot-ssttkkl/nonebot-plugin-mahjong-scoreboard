import enum
from sqlalchemy import Column, Integer, DateTime, String, ForeignKey, func, BigInteger, Enum
from sqlalchemy.orm import relationship

from ml_hitwh.model import OrmBase


class SeasonState(enum.Enum):
    initial = 0
    running = 1
    finished = 2


class SeasonOrm(OrmBase):
    __tablename__ = 'season'

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    group_id = Column('group_id', BigInteger, nullable=False)
    state = Column('state', Enum(SeasonState), default=SeasonState.initial)

    name = Column("name", String)
    code = Column("code", Integer)

    start_time = Column('start_time', DateTime)
    end_time = Column('end_time', DateTime)

    create_time = Column('create_time', DateTime, server_default=func.now())
    delete_time = Column('delete_time', DateTime)

    games = relationship('Game', foreign_keys='Game.season_id', back_populates='season')


class UserSeasonPointOrm(OrmBase):
    __tablename__ = 'user_season_point'

    user_id = Column('user_id', Integer, primary_key=True)
    group_id = Column('group_id', Integer, primary_key=True)

    point = Column('point', Integer, default=0)

    last_change_log_id = Column('last_change_log_id', Integer, ForeignKey("user_season_point_change_log.id"))
    last_change_log = relationship('UserSeasonPointChangeLogOrm',
                                   foreign_keys='UserSeasonPointOrm.last_change_log_id')


class UserSeasonPointChangeType(enum.Enum):
    BY_GAME = 0
    MANUALLY = 1


class UserSeasonPointChangeLogOrm(OrmBase):
    __tablename__ = 'user_season_point_change_log'

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    user_id = Column('user_id', BigInteger, nullable=False)

    season_id = Column('season_id', Integer, ForeignKey("season.id"), nullable=False)
    season = relationship('SeasonOrm', foreign_keys='UserSeasonPointChangeLogOrm.season_id')

    change_type = Column('change_type', Enum(UserSeasonPointChangeType), nullable=False)
    change_point = Column('change_point', Integer, nullable=False)

    related_game_id = Column('related_game_id', Integer, ForeignKey("game.id"))
    related_game = relationship('Game', foreign_keys='UserSeasonPointChangeLogOrm.related_game_id')

    prev_change_log_id = Column('prev_change_log_id', Integer, ForeignKey("user_season_point_change_log.id"))
    prev_change_log = relationship('UserSeasonPointChangeLogOrm',
                                   foreign_keys='UserSeasonPointChangeLogOrm.prev_change_log_id')
