from io import StringIO
from typing import List, Tuple

from nonebot.adapters.onebot.v11 import Message, MessageSegment

from nonebot_plugin_mahjong_scoreboard.controller.mapper import digit_mapping, percentile_str
from nonebot_plugin_mahjong_scoreboard.controller.mapper.season_user_point_mapper import map_point
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


async def map_user_statistics(group: GroupOrm, user: UserOrm, total: int, rates: List[int]) -> Message:
    with StringIO() as sio:
        sio.write(f"用户[{await get_user_nickname(user, group)}]的对战数据如下：\n")

        sio.write(f"  对局数：{total}\n")
        for i, rate in enumerate(rates):
            sio.write(f"  {digit_mapping[i + 1]}位率：{percentile_str(rate)}\n")

        return Message(MessageSegment.text(sio.getvalue().strip()))


async def map_season_user_statistics(group: GroupOrm, user: UserOrm, season: SeasonOrm, total: int, rates: List[int]) -> Message:
    with StringIO() as sio:
        sio.write(f"用户[{await get_user_nickname(user, group)}]在赛季[{season.name}]的对战数据如下：\n")

        sio.write(f"  对局数：{total}\n")
        for i, rate in enumerate(rates):
            sio.write(f"  {digit_mapping[i + 1]}位率：{percentile_str(rate)}\n")

        return Message(MessageSegment.text(sio.getvalue().strip()))
