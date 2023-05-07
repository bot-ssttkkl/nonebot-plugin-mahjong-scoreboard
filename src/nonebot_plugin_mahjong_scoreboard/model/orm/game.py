from datetime import datetime
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, Text, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from nonebot_plugin_mahjong_scoreboard.model.enums import Wind
from ._data_source import data_source
from ..enums import PlayerAndWind, GameState

if TYPE_CHECKING:
    from .group import GroupOrm
    from .season import SeasonOrm
    from .user import UserOrm


@data_source.registry.mapped
class GameOrm:
    __tablename__ = 'games'

    # 应用使用的ID（全局唯一）
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 外部使用的代号（群组内唯一）
    code: Mapped[int]

    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id'))
    group: Mapped["GroupOrm"] = relationship(foreign_keys='GameOrm.group_id')

    promoter_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))
    promoter: Mapped[Optional["UserOrm"]] = relationship(foreign_keys='GameOrm.promoter_user_id')

    season_id: Mapped[Optional[int]] = mapped_column(ForeignKey('seasons.id'))
    season: Mapped[Optional["SeasonOrm"]] = relationship(foreign_keys='GameOrm.season_id')

    player_and_wind: Mapped[PlayerAndWind] = mapped_column(Enum(PlayerAndWind),
                                                           default=PlayerAndWind.four_men_south)
    state: Mapped[GameState] = mapped_column(default=GameState.uncompleted)

    records: Mapped[List["GameRecordOrm"]] = relationship(foreign_keys='GameRecordOrm.game_id',
                                                          back_populates="game")

    progress: Mapped[Optional["GameProgressOrm"]] = relationship(foreign_keys='GameProgressOrm.game_id',
                                                                 uselist=False)

    complete_time: Mapped[Optional[datetime]]

    comment: Mapped[Optional[str]] = mapped_column(Text)

    accessible: Mapped[bool] = mapped_column(default=True)
    create_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    update_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    delete_time: Mapped[Optional[datetime]]

    __table_args__ = (
        Index("games_season_id_idx", "season_id"),
        Index("games_group_id_code_idx", "group_id", "code")
    )


@data_source.registry.mapped
class GameRecordOrm:
    __tablename__ = 'game_records'

    game_id: Mapped[int] = mapped_column(ForeignKey('games.id'), primary_key=True)
    game: Mapped["GameOrm"] = relationship(foreign_keys='GameRecordOrm.game_id',
                                           back_populates='records')

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    user: Mapped["UserOrm"] = relationship(foreign_keys='GameRecordOrm.user_id')

    wind: Mapped[Optional[Wind]]

    score: Mapped[int]  # 分数

    # 真正PT=raw_point*10^point_scale，例如point_scale=0时缩放1x，point_scale=-1时缩放0.1x
    raw_point: Mapped[int] = mapped_column('point', default=0)  # pt
    point_scale: Mapped[int] = mapped_column(default=0)  # pt缩放比例

    @property
    def point(self) -> float:
        return self.raw_point * (10 ** self.point_scale)

    rank: Mapped[Optional[int]] = mapped_column("rnk")  # 排名


@data_source.registry.mapped
class GameProgressOrm:
    __tablename__ = 'game_progresses'

    game_id: Mapped[int] = mapped_column(ForeignKey('games.id'), primary_key=True)
    game: Mapped["GameOrm"] = relationship(foreign_keys='GameProgressOrm.game_id',
                                           back_populates='progress')

    round: Mapped[int]
    honba: Mapped[int]


__all__ = ("GameOrm", "GameRecordOrm", "GameProgressOrm")
