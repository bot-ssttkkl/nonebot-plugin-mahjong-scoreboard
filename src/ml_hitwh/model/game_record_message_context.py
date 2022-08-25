from datetime import datetime

import tzlocal
from beanie import Document
from pymongo import IndexModel


class GameRecordMessageContext(Document):
    message_id: int
    game_id: int
    create_time: datetime = datetime.now(tzlocal.get_localzone())
    extra: dict = {}

    class Settings:
        indexes = [
            IndexModel("message_id", unique=True),
            "game_id",
            IndexModel("create_time", expireAfterSeconds=86400)
        ]
