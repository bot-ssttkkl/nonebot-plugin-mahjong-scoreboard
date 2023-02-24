from io import StringIO
from typing import List, Optional, Tuple

from nonebot.adapters.onebot.v11 import Message, MessageSegment

from nonebot_plugin_mahjong_scoreboard.controller.mapper import season_state_mapping
from nonebot_plugin_mahjong_scoreboard.model.orm import data_source
from nonebot_plugin_mahjong_scoreboard.model.orm.game import GameRecordOrm, GameOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.group import GroupOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.season import SeasonUserPointOrm, SeasonOrm, \
    SeasonUserPointChangeLogOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_user_nickname
from nonebot_plugin_mahjong_scoreboard.utils.rank import ranked


def map_point(point: int, precision: int) -> str:
    point_text = str(point * 10 ** precision)
    if point > 0:
        point_text = f'+{point_text}'
    elif point == 0:
        point_text = f'±{point_text}'
    return point_text


async def map_season_user_point(sup: SeasonUserPointOrm,
                                rank: Optional[int] = None,
                                total: Optional[int] = None) -> Message:
    session = data_source.session()

    user = await session.get(UserOrm, sup.user_id)
    season = await session.get(SeasonOrm, sup.season_id)
    group = await session.get(GroupOrm, season.group_id)

    name = await get_user_nickname(user, group)

    with StringIO() as io:
        # [用户名]在赛季[赛季名]
        # PT：+114
        # 位次：30/36
        io.write(f"[{name}]在赛季[{season.name}]\n")
        io.write(f"PT：{map_point(sup.point, season.config.point_precision)}\n")

        if rank is not None:
            # 位次：+114
            io.write(f'位次：{rank}')
            if total is not None:
                io.write(f'/{total}')

        return Message(MessageSegment.text(io.getvalue().strip()))


async def map_season_user_points(group: GroupOrm, season: SeasonOrm, sups: List[SeasonUserPointOrm]) -> List[Message]:
    session = data_source.session()

    messages = []

    pending = 0
    pending_message = StringIO()

    # 赛季：[赛季名]
    # 状态：进行中
    pending_message.write(f"赛季：{season.name}\n")
    pending_message.write(f"状态：{season_state_mapping[season.state]}\n\n")

    for rank, sup in ranked(sups, key=lambda sup: sup.point, reverse=True):
        user = await session.get(UserOrm, sup.user_id)
        name = await get_user_nickname(user, group)

        line = f"#{rank}  {name}    {map_point(sup.point, season.config.point_precision)}\n"
        pending_message.write(line)
        pending += 1

        if pending >= 10:
            messages.append(Message(MessageSegment.text(pending_message.getvalue().strip())))
            pending = 0
            pending_message = StringIO()

    if pending > 0:
        messages.append(Message(MessageSegment.text(pending_message.getvalue().strip())))

    return messages


async def map_season_user_trend(group: GroupOrm, user: UserOrm, season: SeasonOrm,
                                result: List[Tuple[SeasonUserPointChangeLogOrm, GameOrm, GameRecordOrm]]) -> Message:
    with StringIO() as sio:
        sio.write(f"用户[{await get_user_nickname(user, group)}]在赛季[{season.name}]的最近走势如下：\n")

        for log, game, record in result:
            sio.write(f"  {record.rank}位    {record.score}点  "
                      f"({map_point(record.raw_point, record.point_scale)})  "
                      f"对局{game.code}\n")

        return Message(MessageSegment.text(sio.getvalue().strip()))
