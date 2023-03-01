from io import StringIO
from typing import List, Optional

from nonebot.adapters.onebot.v11 import Message, MessageSegment

from nonebot_plugin_mahjong_scoreboard.controller.mapper import season_state_mapping, map_point
from nonebot_plugin_mahjong_scoreboard.model.orm import data_source
from nonebot_plugin_mahjong_scoreboard.model.orm.group import GroupOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.season import SeasonUserPointOrm, SeasonOrm
from nonebot_plugin_mahjong_scoreboard.model.orm.user import UserOrm
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_user_nickname
from nonebot_plugin_mahjong_scoreboard.utils.rank import ranked


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


async def map_season_user_points(group: GroupOrm, season: SeasonOrm, sups: List[SeasonUserPointOrm],
                                 record_per_msg: int = 10) -> List[Message]:
    session = data_source.session()

    messages = []

    pending = 0
    pending_message = StringIO()

    # 赛季：[赛季名]
    # 状态：进行中
    pending_message.write(f"赛季：{season.name}\n")
    pending_message.write(f"状态：{season_state_mapping[season.state]}\n\n")

    if len(sups) == 0:
        pending_message.write("还没有用户参与该赛季")
        messages.append(Message(MessageSegment.text(pending_message.getvalue().strip())))
        return messages

    for rank, sup in ranked(sups, key=lambda sup: sup.point, reverse=True):
        user = await session.get(UserOrm, sup.user_id)
        name = await get_user_nickname(user, group)

        line = f"#{rank}  {name}    {map_point(sup.point, season.config.point_precision)}\n"
        pending_message.write(line)
        pending += 1

        if 0 < record_per_msg <= pending:
            messages.append(Message(MessageSegment.text(pending_message.getvalue().strip())))
            pending = 0
            pending_message = StringIO()

    if pending > 0:
        messages.append(Message(MessageSegment.text(pending_message.getvalue().strip())))

    return messages
