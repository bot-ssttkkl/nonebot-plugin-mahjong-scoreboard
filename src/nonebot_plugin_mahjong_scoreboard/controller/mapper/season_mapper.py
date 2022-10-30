from io import StringIO
from typing import Optional

from nonebot.adapters.onebot.v11 import Message, MessageSegment

from nonebot_plugin_mahjong_scoreboard.controller.mapper import season_state_mapping, datetime_format
from nonebot_plugin_mahjong_scoreboard.model.orm.season import SeasonOrm


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

        # 半庄战：返点：30000  马点：50 30 -10 -30
        io.write('半庄战：')
        if season.config["south_game_enabled"]:
            io.write('返点：')
            io.write(str(season.config["south_game_origin_point"]))
            io.write(' 马点：')
            for i in season.config["south_game_horse_point"]:
                io.write(str(i))
                io.write(' ')
        else:
            io.write('关闭')
        io.write('\n')

        # 东风战：关闭
        io.write('东风战：')
        if season.config["east_game_enabled"]:
            io.write('返点：')
            io.write(str(season.config["east_game_origin_point"]))
            io.write(' 马点：')
            for i in season.config["east_game_horse_point"]:
                io.write(str(i))
                io.write(' ')
        else:
            io.write('关闭')
        io.write('\n')

        return Message(MessageSegment.text(io.getvalue().strip()))
