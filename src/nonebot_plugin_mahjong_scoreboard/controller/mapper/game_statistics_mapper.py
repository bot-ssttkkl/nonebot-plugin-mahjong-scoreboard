from io import StringIO
from typing import List, Tuple, Optional

from nonebot.adapters.onebot.v11 import Message, MessageSegment

from nonebot_plugin_mahjong_scoreboard.controller.mapper import digit_mapping, percentile_str
from nonebot_plugin_mahjong_scoreboard.controller.mapper.season_user_point_mapper import map_point
from nonebot_plugin_mahjong_scoreboard.model.game_statistics import GameStatistics
from nonebot_plugin_mahjong_scoreboard.model.orm.game import GameRecordOrm, GameOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.group import GroupOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.season import SeasonOrm, \
    SeasonUserPointChangeLogOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_user_nickname


async def map_season_user_trend(group: GroupOrm, user: UserOrm, season: SeasonOrm,
                                result: List[Tuple[SeasonUserPointChangeLogOrm, GameOrm, GameRecordOrm]]) -> Message:
    with StringIO() as sio:
        sio.write(f"用户[{await get_user_nickname(user, group)}]在赛季[{season.name}]的最近走势如下：\n")

        for log, game, record in result:
            sio.write(f"  {record.rank}位    {record.score}点  "
                      f"({map_point(record.raw_point, record.point_scale)})  "
                      f"对局{game.code}\n")

        return Message(MessageSegment.text(sio.getvalue().strip()))


async def map_game_statistics(group: GroupOrm, user: UserOrm, season: Optional[SeasonOrm],
                              game_statistics: GameStatistics) -> Message:
    with StringIO() as sio:
        if season is not None:
            sio.write(f"用户[{await get_user_nickname(user, group)}]在赛季[{season.name}]的对战数据如下：\n")
        else:
            sio.write(f"用户[{await get_user_nickname(user, group)}]的对战数据如下：\n")

        sio.write(f"  对局数：{game_statistics.total} （半庄：{game_statistics.total_south}、东风：{game_statistics.total_east}）\n")
        for i, rate in enumerate(game_statistics.rates):
            sio.write(f"  {digit_mapping[i + 1]}位率：{percentile_str(rate)}\n")
        sio.write(f"  平均顺位：{round(game_statistics.avg_rank, 2)}\n")
        if game_statistics.pt_expectation is not None:
            sio.write(f"  PT期望：{map_point(game_statistics.pt_expectation)}\n")
        sio.write(f"  被飞率：{percentile_str(game_statistics.flying_rate)}")

        return Message(MessageSegment.text(sio.getvalue().strip()))
