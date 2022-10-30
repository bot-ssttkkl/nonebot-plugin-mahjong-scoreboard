# ========== 设置赛季PT ==========
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent
from nonebot.internal.matcher import Matcher

from nonebot_plugin_mahjong_scoreboard.controller.general_handlers import require_group_binding_qq, \
    require_user_binding_qq, require_integer
from nonebot_plugin_mahjong_scoreboard.controller.interceptor import general_interceptor
from nonebot_plugin_mahjong_scoreboard.controller.mapper.season_user_point_mapper import map_season_user_point
from nonebot_plugin_mahjong_scoreboard.controller.utils import split_message, parse_int_or_error
from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.service import season_user_point_service, user_service
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_group_by_binding_qq
from nonebot_plugin_mahjong_scoreboard.service.season_service import get_season_by_id

# ========== 设置赛季PT ==========
set_season_user_point_matcher = on_command("设置赛季PT", aliases={"设置PT", "设置pt", "设置赛季pt"}, priority=5)


@set_season_user_point_matcher.handle()
@general_interceptor(set_season_user_point_matcher)
async def parse_args(event: MessageEvent, matcher: Matcher):
    user_id = None
    point = None

    args = split_message(event.message)[1:]
    for arg in args:
        if arg.type == "at":
            user_id = int(arg.data["qq"])
        elif arg.type == "text":
            point = arg.data["text"]

    if user_id is not None:
        matcher.state["user_binding_qq"] = user_id

    if point is not None:
        point = parse_int_or_error(point, "PT")
        matcher.state["point"] = point


require_group_binding_qq(set_season_user_point_matcher)
require_user_binding_qq(set_season_user_point_matcher)
require_integer(set_season_user_point_matcher, "point", "PT")


@set_season_user_point_matcher.handle()
@general_interceptor(set_season_user_point_matcher)
async def set_season_user_point(event: MessageEvent, matcher: Matcher):
    group_binding_qq = matcher.state["binding_qq"]
    user_binding_qq = matcher.state["user_binding_qq"]
    point = matcher.state["point"]

    group = await get_group_by_binding_qq(group_binding_qq)
    user = await user_service.get_user_by_binding_qq(user_binding_qq)
    operator = await user_service.get_user_by_binding_qq(event.user_id)

    if group.running_season_id is not None:
        season = await get_season_by_id(group.running_season_id)
        sup = await season_user_point_service.change_season_user_point_manually(season, user, point, operator)
        msg = await map_season_user_point(sup)
        msg.append(MessageSegment.text("\n\n设置赛季PT成功"))
        await matcher.send(msg)
    else:
        raise BadRequestError("当前没有运行中的赛季")
