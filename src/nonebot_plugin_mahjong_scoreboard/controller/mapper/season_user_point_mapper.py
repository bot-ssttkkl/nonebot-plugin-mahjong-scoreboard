from io import StringIO
from typing import List, Optional

from nonebot.adapters.onebot.v11 import Message, MessageSegment

from nonebot_plugin_mahjong_scoreboard.controller.mapper import season_state_mapping, digit_mapping
from nonebot_plugin_mahjong_scoreboard.model.orm import data_source
from nonebot_plugin_mahjong_scoreboard.model.orm.game import GameOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.group import GroupOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.season import SeasonUserPointOrm, SeasonOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_user_nickname


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
        io.write(name)
        io.write("在赛季")
        io.write(season.name)
        io.write('\n')

        io.write("PT：")
        if sup.point > 0:
            io.write('+')
        elif sup.point == 0:
            io.write('±')
        io.write(str(sup.point))

        if rank is not None:
            # 位次：+114
            io.write('\n位次：')
            io.write(str(rank))
            if total is not None:
                io.write('/')
                io.write(str(total))

        return Message(MessageSegment.text(io.getvalue()))


async def map_season_user_points(season: SeasonOrm, sups: List[SeasonUserPointOrm]) -> List[Message]:
    session = data_source.session()

    messages = []

    pending = 0
    pending_message = StringIO()

    # 赛季：[赛季名]
    # 状态：进行中
    pending_message.write("赛季：")
    pending_message.write(season.name)
    pending_message.write("\n状态：")
    pending_message.write(season_state_mapping[season.state])
    pending_message.write("\n\n")

    group = await session.get(GroupOrm, season.group_id)

    rank = 1
    for i, sup in enumerate(sups):
        user = await session.get(UserOrm, sup.user_id)
        name = await get_user_nickname(user, group)

        point_text = ""
        if sup.point > 0:
            point_text = '+'
        elif sup.point == 0:
            point_text = '±'
        point_text += str(sup.point)

        # 同分同名次
        if i > 0 and sup.point != sups[i - 1].point:
            rank = i + 1

        line = f"#{rank}  {name}    {point_text}\n"
        pending_message.write(line)
        pending += 1

        if pending >= 10:
            messages.append(Message(MessageSegment.text(pending_message.getvalue().strip())))
            pending = 0
            pending_message = StringIO()

    if pending > 0:
        messages.append(Message(MessageSegment.text(pending_message.getvalue().strip())))

    return messages


async def map_season_user_trend(group: GroupOrm, user: UserOrm, season: SeasonOrm, games: List[GameOrm]) -> Message:
    with StringIO() as sio:
        sio.write("用户")
        sio.write(await get_user_nickname(user, group))
        sio.write("在赛季")
        sio.write(season.name)
        sio.write("的最近走势如下：\n")

        for g in games:
            sio.write("  ")
            sorted_records = sorted(g.records, key=lambda x: x.point, reverse=True)

            for i, r in enumerate(sorted_records):
                if r.user_id == user.id:
                    rank = i + 1
                    record = r
                    break
            else:
                raise ValueError(f"user {user} not in game {g}'s records")

            sio.write(digit_mapping[rank])
            sio.write("位    ")

            sio.write(str(record.score))
            sio.write('点  (')
            if record.point > 0:
                sio.write('+')
            elif r.point == 0:
                sio.write('±')
            sio.write(str(record.point))
            sio.write(')  ')

            sio.write("对局")
            sio.write(str(g.code))
            sio.write("\n")

        return Message(MessageSegment.text(sio.getvalue().strip()))
