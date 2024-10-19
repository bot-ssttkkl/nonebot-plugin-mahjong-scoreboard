from datetime import datetime
from enum import Enum
from typing import Optional, NamedTuple, List

from pydantic import BaseModel, conlist

from .identity import *


class PlayerAndWind(int, Enum):
    four_men_east = 0
    four_men_south = 1


class GameState(int, Enum):
    uncompleted = 0
    completed = 1
    invalid_total_point = 2


class SeasonState(int, Enum):
    initial = 0
    running = 1
    finished = 2


class SeasonUserPointChangeType(int, Enum):
    game = 0
    manually = 1


class Wind(int, Enum):
    east = 0
    south = 1
    west = 2
    north = 3


class RankPointPolicy(int, Enum):
    absolute_rank_point = 1 << 0
    """
    绝对顺位点（PT由顺位唯一确定，与其他策略互斥）
    """

    first_rank_prize = 1 << 1
    """
    头名赏
    """

    horse_point = 1 << 2
    """
    马点
    """

    overwater = 1 << 3
    """
    水上顺位点（日本职业麻将联盟竞技规则，A规）（与其他策略互斥）
    https://www.bilibili.com/read/cv24810368/
    """


class SeasonConfig(BaseModel):
    rank_point_policy: Optional[int] = None
    """
    顺位PT策略
    """

    south_game_enabled: bool
    """
    是否启用半庄战
    """

    south_game_initial_point: Optional[int] = None
    """
    半庄战起点
    """

    south_game_origin_point: Optional[int] = None
    """
    半庄战返点（多于起点的部分将作为头名赏）
    """

    south_game_horse_point: Optional[List[int]] = None
    """
    半庄战顺位点（绝对顺位点或马点）
    """

    south_game_overwater_point: Optional[List[List[int]]] = None
    """
    半庄战水上顺位点
    """

    east_game_enabled: bool
    """
    是否启用东风战
    """

    east_game_initial_point: Optional[int] = None
    """
    东风战起点
    """

    east_game_origin_point: Optional[int] = None
    """
    东风战返点（多于起点的部分将作为头名赏）
    """

    east_game_horse_point: List[int]
    """
    东风战顺位点（绝对顺位点或马点）
    """

    east_game_overwater_point: Optional[List[List[int]]] = None
    """
    东风战水上顺位点
    """

    point_precision: int = 0
    """
    PT精度：精确到10^point_precision
    """


class Season(BaseModel):
    id: int
    group: Group
    state: SeasonState
    code: str
    name: str
    start_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    config: SeasonConfig


class GameRecord(BaseModel):
    user: User
    wind: Optional[Wind] = None
    score: int
    rank: Optional[int] = None
    raw_point: int
    point_scale: int

    @property
    def point(self) -> float:
        return self.raw_point * (10 ** self.point_scale)


class GameProgress(BaseModel):
    round: int
    honba: int


class Game(BaseModel):
    id: int
    code: int
    group: Group
    promoter: Optional[User] = None
    season: Optional[Season] = None
    player_and_wind: PlayerAndWind
    state: GameState
    records: conlist(GameRecord, max_items=4)
    progress: Optional[GameProgress] = None
    complete_time: Optional[datetime] = None
    comment: Optional[str] = None


class SeasonUserPoint(BaseModel):
    user: User
    point: int
    rank: Optional[int] = None
    total: Optional[int] = None


class SeasonUserPointChangeLog(BaseModel):
    user: User
    change_type: SeasonUserPointChangeType
    change_point: int
    related_game: Optional[Game] = None
    create_time: datetime


class GameStatistics(NamedTuple):
    total: int
    total_east: int
    total_south: int
    rates: List[float]
    avg_rank: float
    pt_expectation: Optional[float]
    flying_rate: float


__all__ = ("PlayerAndWind", "GameState", "SeasonState", "SeasonUserPointChangeType", "RankPointPolicy",
           "Wind", "SeasonConfig", "Season", "GameRecord", "GameProgress", "Game",
           "SeasonUserPoint", "SeasonUserPointChangeLog", "GameStatistics")
