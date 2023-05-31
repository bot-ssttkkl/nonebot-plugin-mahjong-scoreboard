from datetime import datetime
from typing import Optional, NamedTuple, List

from pydantic import BaseModel, conlist, Field

from .enums import PlayerAndWind, GameState, Wind, SeasonState, SeasonUserPointChangeType


class User(BaseModel):
    id: int
    platform_user_id: str


class Group(BaseModel):
    id: int
    platform_group_id: str


class SeasonConfig(BaseModel):
    south_game_enabled: bool
    south_game_origin_point: Optional[int]
    south_game_horse_point: Optional[List[int]] = Field(default_factory=list)
    east_game_enabled: bool
    east_game_origin_point: Optional[int]
    east_game_horse_point: Optional[List[int]] = Field(default_factory=list)
    point_precision: int = Field(default=0)  # PT精确到10^point_precision


class Season(BaseModel):
    id: int
    group: Group
    state: SeasonState
    code: str
    name: str
    start_time: Optional[datetime]
    finish_time: Optional[datetime]
    config: SeasonConfig


class GameRecord(BaseModel):
    user: User
    wind: Optional[Wind]
    score: int
    rank: Optional[int]
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
    promoter: Optional[User]
    season: Optional[Season]
    player_and_wind: PlayerAndWind
    state: GameState
    records: conlist(GameRecord, max_items=4)
    progress: Optional[GameProgress]
    complete_time: Optional[datetime]
    comment: Optional[str]


class SeasonUserPoint(BaseModel):
    user: User
    point: int
    rank: Optional[int]
    total: Optional[int]


class SeasonUserPointChangeLog(BaseModel):
    user: User
    change_type: SeasonUserPointChangeType
    change_point: int
    related_game: Optional[Game]
    create_time: datetime


class GameStatistics(NamedTuple):
    total: int
    total_east: int
    total_south: int
    rates: List[float]
    avg_rank: float
    pt_expectation: Optional[float]
    flying_rate: float
