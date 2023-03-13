from collections import UserDict
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import mapped_column, relationship, Mapped

from ._data_source import data_source
from .types.userdict import UserDict as SqlUserDict
from ..enums import SeasonState, SeasonUserPointChangeType
from ...utils.userdict import DictField

if TYPE_CHECKING:
    from .game import GameOrm
    from .group import GroupOrm
    from .user import UserOrm


class SeasonConfig(UserDict):
    south_game_enabled: Mapped[bool] = DictField()
    south_game_origin_point: Mapped[Optional[int]] = DictField(default=None)
    south_game_horse_point: Mapped[Optional[List[int]]] = DictField(default_factory=list)
    east_game_enabled: Mapped[bool] = DictField()
    east_game_origin_point: Mapped[Optional[int]] = DictField(default=None)
    east_game_horse_point: Mapped[Optional[List[int]]] = DictField(default_factory=list)
    point_precision: Mapped[int] = DictField(default=0)  # PT精确到10^point_precision


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

    config: Mapped[SeasonConfig] = mapped_column(SqlUserDict(SeasonConfig))

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


__all__ = ("SeasonOrm", "SeasonUserPointOrm", "SeasonUserPointChangeLogOrm")
