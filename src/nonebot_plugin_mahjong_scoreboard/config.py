from nonebot import get_driver
from pydantic import BaseSettings, root_validator


class Config(BaseSettings):
    mahjong_scoreboard_database_conn_url: str = "sqlite+aiosqlite:///mahjong_scoreboard.db"

    mahjong_scoreboard_callback_host: str = "127.0.0.1"
    mahjong_scoreboard_callback_port: int

    @root_validator(pre=True)
    def callback_validator(cls, values):
        if "mahjong_scoreboard_callback_port" not in values:
            values["mahjong_scoreboard_callback_port"] = values.get("port", None)
        return values

    class Config:
        extra = "ignore"


conf = Config(**get_driver().config.dict())
