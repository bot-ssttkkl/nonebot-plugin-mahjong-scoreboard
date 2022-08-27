from datetime import datetime
from enum import Enum
from typing import Optional

import pymongo
from beanie import Document
from pydantic import conlist, BaseModel
from pymongo import IndexModel


class Wind(Enum):
    EAST = 0
    SOUTH = 1
    WEST = 2
    NORTH = 3


class GameState(Enum):
    uncompleted = 0
    completed = 1
    invalid_total_point = 2


class GameRecord(BaseModel):
    user_id: int
    score: int  # 分数
    point: Optional[float] = None  # pt


class GameModel(BaseModel):
    game_id: int
    group_id: int
    players: int
    wind: Wind
    state: GameState = GameState.uncompleted
    record: conlist(GameRecord, max_items=4) = []
    create_user_id: int
    create_time: datetime


class Game(Document, GameModel):
    class Settings:
        indexes = [
            IndexModel("game_id", unique=True),
            [("group_id", pymongo.ASCENDING), ("record.user_id", pymongo.ASCENDING)],
            [("status", pymongo.ASCENDING), ("create_time", pymongo.ASCENDING)]
        ]
