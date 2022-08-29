from nonebot import get_driver
from pydantic import BaseSettings, conlist


class Config(BaseSettings):
    ml_database_conn_url: str

    # TODO: 支持按群组动态配置
    ml_horse_point_four_men_south: conlist(int, min_items=4, max_items=4) = [50, 10, -10, -30]
    ml_horse_point_four_men_east: conlist(int, min_items=4, max_items=4) = [25, 5, -5, -15]
    ml_horse_point_three_men_south: conlist(int, min_items=3, max_items=3) = [50, 0, -30]
    ml_horse_point_three_men_east: conlist(int, min_items=3, max_items=3) = [50, 0, -30]

    class Config:
        extra = "ignore"


conf = Config(**get_driver().config.dict())
