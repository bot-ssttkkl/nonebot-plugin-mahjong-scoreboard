from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Column, Integer, Enum, DateTime, func, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from . import OrmBase
from ..enums import PlayerAndWind, GameState

if TYPE_CHECKING:
    from .group import GroupOrm
    from .season import SeasonOrm
    from .user import UserOrm


class GameOrm(OrmBase):
    __tablename__ = 'games'

    # 应用使用的ID（全局唯一）
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    # 外部使用的代号（群组内唯一）
    code: int = Column(Integer, nullable=False)

    group_id: int = Column(Integer, ForeignKey('groups.id'), nullable=False)
    group: "GroupOrm" = relationship('GroupOrm', foreign_keys='GameOrm.group_id')

    promoter_user_id: int = Column(Integer, ForeignKey('users.id'))
    promoter: "UserOrm" = relationship('UserOrm', foreign_keys='GameOrm.promoter_user_id')

    season_id: int = Column(Integer, ForeignKey('seasons.id'))
    season: "SeasonOrm" = relationship('SeasonOrm', foreign_keys='GameOrm.season_id')

    player_and_wind: PlayerAndWind = Column(Enum(PlayerAndWind), nullable=False,
                                            default=PlayerAndWind.four_men_south)
    state: GameState = Column(Enum(GameState), nullable=False, default=GameState.uncompleted)

    records: List["GameRecordOrm"] = relationship("GameRecordOrm",
                                                  foreign_keys='GameRecordOrm.game_id',
                                                  back_populates="game")

    accessible: bool = Column(Boolean, nullable=False, default=True)
    create_time: datetime = Column(DateTime, nullable=False, server_default=func.now())
    update_time: datetime = Column(DateTime)
    delete_time: datetime = Column(DateTime)


class GameRecordOrm(OrmBase):
    __tablename__ = 'game_records'

    game_id: int = Column(Integer, ForeignKey('games.id'), primary_key=True, nullable=False)
    game: "GameOrm" = relationship('GameOrm', foreign_keys='GameRecordOrm.game_id', back_populates='records')

    user_id: int = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    user: "UserOrm" = relationship('UserOrm', foreign_keys='GameRecordOrm.user_id')

    score: int = Column(Integer, nullable=False)  # 分数
    point: int = Column(Integer, nullable=False, default=0)  # pt


__all__ = ("GameOrm", "GameRecordOrm")
