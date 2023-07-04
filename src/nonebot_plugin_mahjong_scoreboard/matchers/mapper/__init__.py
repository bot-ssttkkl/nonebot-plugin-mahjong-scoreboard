from datetime import datetime
from typing import Union

import pytz
import tzlocal

from nonebot_plugin_mahjong_scoreboard.model.enums import PlayerAndWind, GameState, SeasonState, Wind

player_and_wind_mapping = {
    PlayerAndWind.four_men_east: '四人东',
    PlayerAndWind.four_men_south: '四人南'
}

game_state_mapping = {
    GameState.uncompleted: '未完成',
    GameState.completed: '已完成',
    GameState.invalid_total_point: '分数冲突'
}

season_state_mapping = {
    SeasonState.initial: '未开始',
    SeasonState.running: '进行中',
    SeasonState.finished: '已结束'
}

wind_mapping = {
    Wind.east: '东',
    Wind.south: '南',
    Wind.west: '西',
    Wind.north: '北'
}

digit_mapping = {
    1: '一',
    2: '二',
    3: '三',
    4: '四',
}

datetime_format = '%Y-%m-%d %H:%M'


def map_datetime(dt: datetime):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)
    return dt.astimezone(tzlocal.get_localzone()).strftime(datetime_format)


def percentile_str(x: float, ndigits: int = 2) -> str:
    return f'{round(x * 100, ndigits)}%'


def map_point(raw_point: Union[int, float], scale: int = 0) -> str:
    return map_real_point(raw_point * 10 ** scale, scale)


def map_real_point(point: Union[int, float], precision: int = 0) -> str:
    point_text = f"%.{precision}f" % point
    if point > 0:
        point_text = f'+{point_text}'
    elif point == 0:
        point_text = f'±{point_text}'
    return point_text
