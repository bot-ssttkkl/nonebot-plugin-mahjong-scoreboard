from pathlib import Path
from typing import Any

import nonebot_plugin_localstore as store
from nonebot import get_plugin_config
from nonebot.compat import PYDANTIC_V2
from pydantic import BaseModel


def _get_default_sql_conn_url():
    # 旧版本的sqlite数据库在working directory
    data_file = Path("mahjong_scoreboard.db")
    if not data_file.exists():
        data_file = store.get_data_file("nonebot_plugin_mahjong_scoreboard", "mahjong_scoreboard.db")

    return "sqlite+aiosqlite:///" + str(data_file)


def compatible_model_pre_validator(func):
    if PYDANTIC_V2:
        from pydantic import model_validator

        @model_validator(mode='before')
        @classmethod
        def checker(cls, values: dict[str]):
            return func(cls, values)

        return checker
    else:
        from pydantic import root_validator
        return root_validator(pre=True, allow_reuse=True)(func)


class Config(BaseModel):
    mahjong_scoreboard_database_conn_url: str
    mahjong_scoreboard_send_forward_message: bool = True
    mahjong_scoreboard_send_image: bool = False
    mahjong_scoreboard_enable_permission_check: bool = True

    @compatible_model_pre_validator
    def default_sql_conn_url(cls, values: dict[str, Any]):
        if "mahjong_scoreboard_database_conn_url" not in values:
            values["mahjong_scoreboard_database_conn_url"] = _get_default_sql_conn_url()
        return values

    class Config:
        extra = "ignore"


conf = get_plugin_config(Config)
