from nonebot import get_driver
from pydantic import BaseSettings


class Config(BaseSettings):
    ml_database_conn_url: str

    class Config:
        extra = "ignore"


conf = Config(**get_driver().config.dict())
