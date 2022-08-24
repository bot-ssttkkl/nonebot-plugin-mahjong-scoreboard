from nonebot import get_driver
from pydantic import BaseSettings


class Config(BaseSettings):
    ml_mongo_conn_url: str
    ml_mongo_database_name: str

    class Config:
        extra = "ignore"


conf = Config(**get_driver().config.dict())
