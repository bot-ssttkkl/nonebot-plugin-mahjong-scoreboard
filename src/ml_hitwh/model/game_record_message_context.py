from datetime import datetime

import tzlocal
from beanie import Document
from pydantic import BaseModel
from pymongo import IndexModel


class GameRecordMessageContextModel(BaseModel):
    message_id: int
    game_id: int
    create_time: datetime = datetime.now(tzlocal.get_localzone())
    extra: dict = {}


class GameRecordMessageContext(Document, GameRecordMessageContextModel):
    class Settings:
        indexes = [
            IndexModel("message_id", unique=True),
            "game_id",
            IndexModel("create_time", expireAfterSeconds=86400)
        ]
