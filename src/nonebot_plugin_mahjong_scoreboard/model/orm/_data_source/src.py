from urllib.parse import urlparse

from nonebot import get_driver, require

from nonebot_plugin_mahjong_scoreboard.config import conf

require("nonebot_plugin_sqlalchemy")
from nonebot_plugin_sqlalchemy import DataSource

data_source = DataSource(get_driver(), conf.mahjong_scoreboard_database_conn_url)


def _detect_dialect():
    url = urlparse(conf.mahjong_scoreboard_database_conn_url)
    if '+' in url.scheme:
        return url.scheme.split('+')[0]
    else:
        return url.scheme


dialect = _detect_dialect()

__all__ = ("data_source", "dialect")
