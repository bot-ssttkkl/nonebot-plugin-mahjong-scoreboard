from datetime import datetime
from typing import Optional, List

from sqlalchemy import ForeignKey, Index, Enum, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship

from ._data_source import data_source
from .types.pydantic import PydanticModel
from ..model import SeasonState, SeasonConfig, SeasonUserPointChangeType, PlayerAndWind, GameState, Wind


@data_source.registry.mapped
class UserOrm:
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    platform_user_id: Mapped[str] = mapped_column(index=True)


@data_source.registry.mapped
class GroupOrm:
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    platform_group_id: Mapped[str] = mapped_column(index=True)

    running_season_id: Mapped[Optional[int]] = mapped_column(ForeignKey('seasons.id'))
    running_season: Mapped[Optional['SeasonOrm']] = relationship(foreign_keys='GroupOrm.running_season_id')

    prev_game_code_base: Mapped[int] = mapped_column(default=0)
    prev_game_code_identifier: Mapped[int] = mapped_column(default=0)


@data_source.registry.mapped
class SeasonOrm:
    __tablename__ = 'seasons'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id'))
    group: Mapped['GroupOrm'] = relationship(foreign_keys='SeasonOrm.group_id')

    state: Mapped[SeasonState] = mapped_column(default=SeasonState.initial)

    code: Mapped[str]
    name: Mapped[str]

    start_time: Mapped[Optional[datetime]]
    finish_time: Mapped[Optional[datetime]]

    config: Mapped[SeasonConfig] = mapped_column(PydanticModel(SeasonConfig))

    accessible: Mapped[bool] = mapped_column(default=True)
    create_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    update_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    delete_time: Mapped[Optional[datetime]]

    __table_args__ = (
        Index("seasons_group_id_code_idx", "group_id", "code"),
    )


@data_source.registry.mapped
class SeasonUserPointOrm:
    __tablename__ = 'season_user_points'

    season_id: Mapped[int] = mapped_column(ForeignKey('seasons.id'), primary_key=True)
    season: Mapped['SeasonOrm'] = relationship(foreign_keys='SeasonUserPointOrm.season_id')

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    user: Mapped['UserOrm'] = relationship(foreign_keys='SeasonUserPointOrm.user_id')

    point: Mapped[int] = mapped_column(default=0)

    create_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    update_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)


@data_source.registry.mapped
class SeasonUserPointChangeLogOrm:
    __tablename__ = 'season_user_point_change_logs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    season_id: Mapped[int] = mapped_column(ForeignKey('seasons.id'))
    season: Mapped['SeasonOrm'] = relationship(foreign_keys='SeasonUserPointChangeLogOrm.season_id')

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['UserOrm'] = relationship(foreign_keys='SeasonUserPointChangeLogOrm.user_id')

    change_type: Mapped[SeasonUserPointChangeType]
    change_point: Mapped[int]

    related_game_id: Mapped[Optional[int]] = mapped_column(ForeignKey('games.id'))
    related_game: Mapped[Optional['GameOrm']] = relationship(foreign_keys='SeasonUserPointChangeLogOrm.related_game_id')

    create_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        Index("seasons_related_game_id_idx", "related_game_id"),
    )


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
                                                          back_populates="game",
                                                          lazy="selectin")

    progress: Mapped[Optional["GameProgressOrm"]] = relationship(foreign_keys='GameProgressOrm.game_id',
                                                                 uselist=False,
                                                                 lazy="joined")

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
