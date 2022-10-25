from io import StringIO
from typing import List

from nonebot.adapters.onebot.v11 import Message, MessageSegment

from ml_hitwh.model.orm import data_source
from ml_hitwh.model.orm.group import GroupOrm
from ml_hitwh.model.orm.season import SeasonUserPointOrm, SeasonOrm
from ml_hitwh.model.orm.user import UserOrm
from ml_hitwh.service.group_service import get_user_nickname


async def map_season_user_point(sup: SeasonUserPointOrm, rank: int, total: int) -> Message:
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

        # 位次：+114
        io.write('\n位次：')
        io.write(str(rank))
        io.write('/')
        io.write(str(total))

        return Message(MessageSegment.text(io.getvalue()))


async def map_season_user_points(sups: List[SeasonUserPointOrm]) -> List[Message]:
    session = data_source.session()

    messages = []
    pending_message = Message()

    group = None
    season = None

    for i, sup in enumerate(sups):
        if season is None:
            season = await session.get(SeasonOrm, sup.season_id)
        if group is None:
            group = await session.get(GroupOrm, season.group_id)

        user = await session.get(UserOrm, sup.user_id)
        name = await get_user_nickname(user, group)

        point_text = ""
        if sup.point > 0:
            point_text = '+'
        elif sup.point == 0:
            point_text = '±'
        point_text += str(sup.point)

        line = f"#{i + 1}\t{name}\t{point_text}\n"
        pending_message.append(MessageSegment.text(line))

        if len(pending_message) >= 10:
            messages.append(pending_message)
            pending_message = Message()

    if len(pending_message) > 0:
        messages.append(pending_message)

    return messages
