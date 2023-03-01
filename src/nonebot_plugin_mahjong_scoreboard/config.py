from nonebot import get_driver
from pydantic import BaseSettings


class Config(BaseSettings):
    mahjong_scoreboard_database_conn_url: str = "sqlite+aiosqlite:///mahjong_scoreboard.db"
    mahjong_scoreboard_send_forward_message: bool = True

    class Config:
        extra = "ignore"


conf = Config(**get_driver().config.dict())
