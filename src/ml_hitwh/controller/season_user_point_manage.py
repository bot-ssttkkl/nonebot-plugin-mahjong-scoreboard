# ========== 设置赛季PT ==========
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.internal.matcher import Matcher

from ml_hitwh.controller.interceptor import general_interceptor
from ml_hitwh.controller.mapper.season_user_point_mapper import map_season_user_point
from ml_hitwh.controller.utils import split_message, parse_int_or_error
from ml_hitwh.errors import BadRequestError
from ml_hitwh.service import season_user_point_service, user_service
from ml_hitwh.service.group_service import get_group_by_binding_qq
from ml_hitwh.service.season_service import get_season_by_id

set_season_user_point_matcher = on_command("设置赛季PT", aliases={"设置PT", "设置pt", "设置赛季pt"}, priority=5)


@set_season_user_point_matcher.handle()
@general_interceptor(set_season_user_point_matcher)
async def set_season_user_point(event: GroupMessageEvent, matcher: Matcher):
    user_id = event.user_id
    point = None

    args = split_message(event.message)[1:]
    for arg in args:
        if arg.type == "at":
            user_id = int(arg.data["qq"])
        elif arg.type == "text":
            point = arg.data["text"]

    point = parse_int_or_error(point, "PT")

    group = await get_group_by_binding_qq(event.group_id)
    user = await user_service.get_user_by_binding_qq(user_id)
    operator = await user_service.get_user_by_binding_qq(event.user_id)

    if group.running_season_id is not None:
        season = await get_season_by_id(group.running_season_id)
        sup = await season_user_point_service.change_season_user_point_manually(season, user, point, operator)
        msg = await map_season_user_point(sup)
        msg.append(MessageSegment.text("\n\n设置赛季PT成功"))
        await matcher.send(msg)
    else:
        raise BadRequestError("当前没有运行中的赛季")
