from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, MessageEvent, GroupMessageEvent
from nonebot.internal.matcher import Matcher

from nonebot_plugin_mahjong_scoreboard.controller.general_handlers import require_group_binding_qq, \
    require_parse_unary_text_arg
from nonebot_plugin_mahjong_scoreboard.controller.interceptor import general_interceptor
from nonebot_plugin_mahjong_scoreboard.controller.mapper.season_mapper import map_season
from nonebot_plugin_mahjong_scoreboard.controller.utils import send_group_forward_msg, send_private_forward_msg
from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.service import season_service
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_group_by_binding_qq

# ========== 查询赛季 ==========
query_season_matcher = on_command("查询赛季", aliases={"赛季", "当前赛季"}, priority=5)

require_parse_unary_text_arg(query_season_matcher, "season_code")
require_group_binding_qq(query_season_matcher)


@query_season_matcher.handle()
@general_interceptor(query_season_matcher)
async def query_running_season(matcher: Matcher):
    group = await get_group_by_binding_qq(matcher.state["binding_qq"])

    season_code = matcher.state.get("season_code", None)
    if season_code:
        season = await season_service.get_season_by_code(season_code, group)
        if season is None:
            raise BadRequestError("找不到指定赛季")
    else:
        if group.running_season_id:
            season = await season_service.get_season_by_id(group.running_season_id)
        else:
            raise BadRequestError("当前没有运行中的赛季")

    msg = map_season(season, group_info=matcher.state["group_info"])
    await matcher.send(msg)


# ========== 查询所有赛季 ==========
query_all_seasons_matcher = on_command("查询所有赛季", aliases={"所有赛季"}, priority=5)

require_group_binding_qq(query_all_seasons_matcher)


@query_all_seasons_matcher.handle()
@general_interceptor(query_all_seasons_matcher)
async def query_all_seasons(bot: Bot, event: MessageEvent, matcher: Matcher):
    group = await get_group_by_binding_qq(matcher.state["binding_qq"])
    seasons = await season_service.get_all_seasons(group)

    if len(seasons) != 0:
        group_info = await bot.get_group_info(group_id=group.binding_qq)
        header = Message([
            MessageSegment.text(f"以下是群组{group_info['group_name']}({group_info['group_id']})的最近对局")
        ])
        messages = [header]
        for s in seasons:
            messages.append(map_season(s))

        if isinstance(event, GroupMessageEvent):
            await send_group_forward_msg(bot, event.group_id, messages)
        else:
            await send_private_forward_msg(bot, event.user_id, messages)
    else:
        await matcher.send("你还没有进行过对局")
