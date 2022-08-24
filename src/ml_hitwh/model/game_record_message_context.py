from datetime import datetime

from beanie import Document
from pymongo import IndexModel


class GameRecordMessageContext(Document):
    message_id: int
    game_id: int
    create_time: datetime
    extra: dict = {}

    class Settings:
        indexes = [
            IndexModel("message_id", unique=True),
            "game_id",
            IndexModel("create_time", expireAfterSeconds=86400)
        ]
