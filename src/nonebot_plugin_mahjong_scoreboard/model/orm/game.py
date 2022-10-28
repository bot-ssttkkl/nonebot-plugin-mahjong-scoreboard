from datetime import datetime
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import Column, Integer, Enum, DateTime, func, Boolean, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

from nonebot_plugin_mahjong_scoreboard.model.enums import Wind
from . import data_source
from ..enums import PlayerAndWind, GameState

if TYPE_CHECKING:
    from .group import GroupOrm
    from .season import SeasonOrm
    from .user import UserOrm


@data_source.registry.mapped
class GameOrm:
    __tablename__ = 'games'

    # 应用使用的ID（全局唯一）
    id: int = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    # 外部使用的代号（群组内唯一）
    code: int = Column(Integer, nullable=False)

    group_id: int = Column(Integer, ForeignKey('groups.id'), nullable=False)
    group: "GroupOrm" = relationship('GroupOrm', foreign_keys='GameOrm.group_id')

    promoter_user_id: Optional[int] = Column(Integer, ForeignKey('users.id'))
    promoter: Optional["UserOrm"] = relationship('UserOrm', foreign_keys='GameOrm.promoter_user_id')

    season_id: Optional[int] = Column(Integer, ForeignKey('seasons.id'))
    season: Optional["SeasonOrm"] = relationship('SeasonOrm', foreign_keys='GameOrm.season_id')

    player_and_wind: PlayerAndWind = Column(Enum(PlayerAndWind), nullable=False,
                                            default=PlayerAndWind.four_men_south)
    state: GameState = Column(Enum(GameState), nullable=False, default=GameState.uncompleted)

    records: List["GameRecordOrm"] = relationship("GameRecordOrm",
                                                  foreign_keys='GameRecordOrm.game_id',
                                                  back_populates="game")

    progress: Optional["GameProgressOrm"] = relationship("GameProgressOrm",
                                                         foreign_keys='GameProgressOrm.game_id',
                                                         uselist=False)

    complete_time: Optional[datetime] = Column(DateTime)

    comment: Optional[str] = Column(Text)

    accessible: bool = Column(Boolean, nullable=False, default=True)
    create_time: datetime = Column(DateTime, nullable=False, server_default=func.now())
    update_time: datetime = Column(DateTime, nullable=False, server_default=func.now())
    delete_time: Optional[datetime] = Column(DateTime)

    __table_args__ = (
        Index("games_season_id_idx", "season_id"),
        Index("games_group_id_code_idx", "group_id", "code")
    )


@data_source.registry.mapped
class GameRecordOrm:
    __tablename__ = 'game_records'

    game_id: int = Column(Integer, ForeignKey('games.id'), primary_key=True, nullable=False)
    game: "GameOrm" = relationship('GameOrm', foreign_keys='GameRecordOrm.game_id', back_populates='records')

    user_id: int = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    user: "UserOrm" = relationship('UserOrm', foreign_keys='GameRecordOrm.user_id')

    wind: Optional[Wind] = Column(Enum(Wind))

    score: int = Column(Integer, nullable=False)  # 分数
    point: int = Column(Integer, nullable=False, default=0)  # pt


@data_source.registry.mapped
class GameProgressOrm:
    __tablename__ = 'game_progresses'

    game_id: int = Column(Integer, ForeignKey('games.id'), primary_key=True, nullable=False)
    game: "GameOrm" = relationship('GameOrm', foreign_keys='GameProgressOrm.game_id', back_populates='progress')

    round: int = Column(Integer, nullable=False)
    honba: int = Column(Integer, nullable=False)


__all__ = ("GameOrm", "GameRecordOrm", "GameProgressOrm")
