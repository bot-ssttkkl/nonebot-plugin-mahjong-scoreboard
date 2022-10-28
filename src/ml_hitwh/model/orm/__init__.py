from nonebot import get_driver, require

from ml_hitwh.config import conf

require("nonebot_plugin_sqlalchemy")
from nonebot_plugin_sqlalchemy import DataSource

data_source = DataSource(get_driver(), conf.ml_database_conn_url)

__all__ = ("data_source",)
