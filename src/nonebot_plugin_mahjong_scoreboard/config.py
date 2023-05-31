from pathlib import Path

import nonebot_plugin_localstore as store
from nonebot import get_driver
from pydantic import BaseSettings, root_validator


def _get_default_sql_conn_url():
    # 旧版本的sqlite数据库在working directory
    data_file = Path("mahjong_scoreboard.db")
    if not data_file.exists():
        data_file = store.get_data_file("nonebot_plugin_mahjong_scoreboard", "mahjong_scoreboard.db")

    return "sqlite+aiosqlite:///" + str(data_file)


class Config(BaseSettings):
    mahjong_scoreboard_database_conn_url: str
    mahjong_scoreboard_send_forward_message: bool = True
    mahjong_scoreboard_enable_permission_check: bool = True

    @root_validator(pre=True, allow_reuse=True)
    def default_sql_conn_url(cls, values):
        if "mahjong_scoreboard_database_conn_url" not in values:
            values["mahjong_scoreboard_database_conn_url"] = _get_default_sql_conn_url()
        return values

    class Config:
        extra = "ignore"


conf = Config(**get_driver().config.dict())
