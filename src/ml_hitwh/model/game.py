import enum

from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, BigInteger, Enum
from sqlalchemy.orm import relationship

from ml_hitwh.model import OrmBase


class PlayerAndWind(enum.Enum):
    FOUR_MEN_EAST = 1
    FOUR_MEN_SOUTH = 2
    THREE_MEN_EAST = 3
    THREE_MEN_SOUTH = 4


class GameState(enum.Enum):
    uncompleted = 1
    completed = 2
    invalid_total_point = 3


class Game(OrmBase):
    __tablename__ = 'game'

    # 应用使用的ID
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    # 外部使用的代号
    code = Column('code', Integer, nullable=False)
    group_id = Column('group_id', BigInteger, nullable=False)
    create_user_id = Column('create_user_id', BigInteger)

    season_id = Column('season_id', Integer, ForeignKey("season.id"))
    season = relationship('SeasonOrm', foreign_keys='Game.season_id', back_populates='games')

    player_and_wind = Column('player_and_wind', Enum(PlayerAndWind), nullable=False,
                             default=PlayerAndWind.FOUR_MEN_SOUTH)
    state = Column('state', Enum(GameState), nullable=False, default=GameState.uncompleted)

    create_time = Column('create_time', DateTime, nullable=False, server_default=func.now())
    delete_time = Column('delete_time', DateTime)

    records = relationship("GameRecord", foreign_keys='GameRecord.game_id', back_populates="game")


class GameRecord(OrmBase):
    __tablename__ = 'game_record'

    id = Column('id', Integer, primary_key=True, autoincrement=True)

    game_id = Column('game_id', Integer, ForeignKey("game.id"), nullable=False)
    game = relationship('Game', foreign_keys='GameRecord.game_id', back_populates='records')

    user_id = Column('user_id', BigInteger, nullable=False)
    score = Column('score', Integer, nullable=False)  # 分数
    point = Column('point', Integer)  # pt
