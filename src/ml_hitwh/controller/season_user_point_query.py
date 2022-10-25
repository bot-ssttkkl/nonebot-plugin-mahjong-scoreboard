from io import StringIO

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.internal.matcher import Matcher

from ml_hitwh.controller.interceptor import general_interceptor
from ml_hitwh.controller.mapper.season_user_point_mapper import map_season_user_point
from ml_hitwh.controller.utils import split_message
from ml_hitwh.errors import BadRequestError
from ml_hitwh.service import season_user_point_service
from ml_hitwh.service.group_service import get_group_by_binding_qq
from ml_hitwh.service.season_service import get_season_by_id
from ml_hitwh.service.season_user_point_service import get_season_user_point_rank, count_season_user_point
from ml_hitwh.service.user_service import get_user_by_binding_qq

query_season_point = on_command("查询PT", aliases={"PT", "pt"}, priority=5)


@query_season_point.handle()
@general_interceptor(query_season_point)
async def query_season_user_point(event: GroupMessageEvent, matcher: Matcher):
    user_id = event.user_id

    args = split_message(event.message)
    if len(args) > 1 and args[1].type == 'at':
        user_id = int(args[1].data["qq"])

    group = await get_group_by_binding_qq(event.group_id)
    user = await get_user_by_binding_qq(user_id)

    if group.running_season_id is not None:
        season = await get_season_by_id(group.running_season_id)
        sup = await season_user_point_service.get_season_user_point(season, user)
        if sup is None:
            raise BadRequestError("你还没有参加过对局")

        rank = await get_season_user_point_rank(sup)
        total = await count_season_user_point(season)

        with StringIO() as sio:
            await map_season_user_point(sio, sup, rank, total)
            msg = sio.getvalue().strip()
            await matcher.send(msg)
    else:
        raise BadRequestError("当前没有运行中的赛季")
