from io import StringIO
from typing import Optional

from nonebot.adapters.onebot.v11 import Message, MessageSegment

from ml_hitwh.controller.mapper import season_state_mapping, datetime_format
from ml_hitwh.model.orm.season import SeasonOrm


def map_season(season: SeasonOrm, *, group_info: Optional[dict] = None) -> Message:
    with StringIO() as io:
        # {season.name}
        io.write(season.name)
        io.write('\n')

        # 代号：{season.code}
        io.write('代号：')
        io.write(season.code)
        io.write('\n')

        if group_info is not None:
            # 群组：义已死吾亦死 (114514)
            io.write('群组：')
            io.write(group_info["group_name"])
            io.write(' (')
            io.write(str(group_info["group_id"]))
            io.write(')\n')

        if season.state:
            io.write('状态：')
            io.write(season_state_mapping[season.state])
            io.write('\n')

        if season.start_time:
            io.write('开始时间：')
            io.write(season.start_time.strftime(datetime_format))
            io.write('\n')

        if season.finish_time:
            io.write('结束时间：')
            io.write(season.finish_time.strftime(datetime_format))
            io.write('\n')

        # 半庄战：开启
        io.write('半庄战：')
        if season.south_game_enabled:
            io.write('开启')
        else:
            io.write('关闭')
        io.write('\n')

        if season.south_game_enabled:
            # 半庄战马点：50 30 -10 -30
            io.write('半庄战马点：')
            for i in season.south_game_horse_point:
                io.write(str(i))
                io.write(' ')
            io.write('\n')

        # 东风战：关闭
        io.write('东风战：')
        if season.east_game_enabled:
            io.write('开启')
        else:
            io.write('关闭')
        io.write('\n')

        if season.east_game_enabled:
            # 东风马点：25 15 -5 -15
            io.write('半庄战马点：')
            for i in season.east_game_horse_point:
                io.write(str(i))
                io.write(' ')
            io.write('\n')

        return Message(MessageSegment.text(io.getvalue()))
