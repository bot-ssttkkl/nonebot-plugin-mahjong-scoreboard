from nonebot import get_driver
from nonebot_plugin_sqlalchemy import DataSource

from nonebot_plugin_mahjong_scoreboard.config import conf

data_source = DataSource(get_driver(), conf.mahjong_scoreboard_database_conn_url)

__all__ = ("data_source",)
