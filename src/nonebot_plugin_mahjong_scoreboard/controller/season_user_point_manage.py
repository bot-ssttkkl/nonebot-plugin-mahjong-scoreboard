from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent, Message
from nonebot.internal.matcher import Matcher

from nonebot_plugin_mahjong_scoreboard.controller.general_handlers import require_group_binding_qq, \
    require_user_binding_qq, require_float, require_parse_unary_at_arg, require_running_season
from nonebot_plugin_mahjong_scoreboard.controller.interceptor import general_interceptor
from nonebot_plugin_mahjong_scoreboard.controller.mapper.season_user_point_mapper import map_season_user_point
from nonebot_plugin_mahjong_scoreboard.controller.utils.message import SplitCommandArgs
from nonebot_plugin_mahjong_scoreboard.controller.utils.parse import parse_float_or_error
from nonebot_plugin_mahjong_scoreboard.service import season_user_point_service, user_service
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_group_by_binding_qq, get_user_nickname
from nonebot_plugin_mahjong_scoreboard.service.season_service import get_season_by_id
from nonebot_plugin_mahjong_scoreboard.service.season_user_point_service import reset_season_user_point
from nonebot_plugin_mahjong_scoreboard.service.user_service import get_user_by_binding_qq


async def parse_args(matcher: Matcher, args: Message):
    user_id = None
    point = None

    for arg in args:
        if arg.type == "at":
            user_id = int(arg.data["qq"])
        elif arg.type == "text":
            point = arg.data["text"]

    if user_id is not None:
        matcher.state["user_binding_qq"] = user_id

    if point is not None:
        point = parse_float_or_error(point, "PT")
        matcher.state["point"] = point


# ========== 设置用户PT ==========
set_season_user_point_matcher = on_command("设置用户PT", aliases={"设置用户pt", "设置PT", "设置pt"}, priority=5)


@set_season_user_point_matcher.handle()
@general_interceptor(set_season_user_point_matcher)
async def parse_set_season_user_point_args(matcher: Matcher, args: Message = SplitCommandArgs()):
    await parse_args(matcher, args)


require_group_binding_qq(set_season_user_point_matcher)
require_user_binding_qq(set_season_user_point_matcher, sender_as_default_on_group_msg=False)
require_float(set_season_user_point_matcher, "point", "PT")
require_running_season(set_season_user_point_matcher)


@set_season_user_point_matcher.handle()
@general_interceptor(set_season_user_point_matcher)
async def reset_season_user_point_confirm(matcher: Matcher):
    user = await get_user_by_binding_qq(matcher.state["user_binding_qq"])
    group = await get_group_by_binding_qq(matcher.state["binding_qq"])

    await matcher.pause(f"确定设置用户[{await get_user_nickname(user, group)}]PT为{matcher.state['point']}吗？(y/n)")


@set_season_user_point_matcher.handle()
@general_interceptor(set_season_user_point_matcher)
async def set_season_user_point(event: MessageEvent, matcher: Matcher):
    user = await get_user_by_binding_qq(matcher.state["user_binding_qq"])
    operator = await get_user_by_binding_qq(event.user_id)

    if event.message.extract_plain_text() == 'y':
        season = await get_season_by_id(matcher.state["running_season_id"])
        sup = await season_user_point_service.change_season_user_point_manually(season, user,
                                                                                matcher.state["point"],
                                                                                operator)
        msg = await map_season_user_point(sup)
        msg.append(MessageSegment.text("\n\n设置用户PT成功"))
        await matcher.send(msg)
    else:
        await matcher.finish("取消设置用户PT")


# ========== 重置用户PT ==========
reset_season_user_point_matcher = on_command("重置用户PT", aliases={"重置用户pt", "重置PT", "重置pt"}, priority=5)

require_parse_unary_at_arg(reset_season_user_point_matcher, "user_binding_qq")
require_group_binding_qq(reset_season_user_point_matcher)
require_user_binding_qq(reset_season_user_point_matcher, sender_as_default_on_group_msg=False)
require_running_season(reset_season_user_point_matcher)


@reset_season_user_point_matcher.handle()
@general_interceptor(reset_season_user_point_matcher)
async def confirm_reset_season_user_point(matcher: Matcher):
    user = await get_user_by_binding_qq(matcher.state["user_binding_qq"])
    group = await get_group_by_binding_qq(matcher.state["binding_qq"])

    await matcher.pause(f"确定重置用户[{await get_user_nickname(user, group)}]PT吗？(y/n)")


@reset_season_user_point_matcher.handle()
@general_interceptor(reset_season_user_point_matcher)
async def handle_reset_season_user_point(event: MessageEvent, matcher: Matcher):
    if event.message.extract_plain_text() == 'y':
        user = await user_service.get_user_by_binding_qq(matcher.state["user_binding_qq"])
        operator = await user_service.get_user_by_binding_qq(event.user_id)

        season = await get_season_by_id(matcher.state["running_season_id"])
        await reset_season_user_point(season, user, operator)
        await matcher.send("重置用户PT成功")
    else:
        await matcher.finish("取消重置用户PT")
