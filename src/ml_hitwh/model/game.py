from datetime import datetime
from enum import Enum

import pymongo
from beanie import Document
from pydantic import conlist, BaseModel
from pymongo import IndexModel


class GameState(Enum):
    uncompleted = 0
    completed = 1
    invalid_total_point = 2


class GameRecord(BaseModel):
    user_id: int
    point: int


class Game(Document):
    game_id: int
    group_id: int
    state: GameState = GameState.uncompleted
    record: conlist(GameRecord, max_items=4) = []
    create_user_id: int
    create_time: datetime

    class Settings:
        indexes = [
            IndexModel("game_id", unique=True),
            [("group_id", pymongo.ASCENDING), ("record.user_id", pymongo.ASCENDING)],
            [("status", pymongo.ASCENDING), ("create_time", pymongo.ASCENDING)]
        ]
