from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.internal.matcher import Matcher

from nonebot_plugin_mahjong_scoreboard.controller.general_handlers import require_group_binding_qq, \
    require_user_binding_qq, require_parse_unary_at_arg, require_parse_unary_text_arg, require_running_season
from nonebot_plugin_mahjong_scoreboard.controller.interceptor import general_interceptor
from nonebot_plugin_mahjong_scoreboard.controller.mapper.season_user_point_mapper import map_season_user_point, \
    map_season_user_points
from nonebot_plugin_mahjong_scoreboard.controller.utils.send_messages import send_msgs
from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.service import season_user_point_service, season_service
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_group_by_binding_qq
from nonebot_plugin_mahjong_scoreboard.service.season_service import get_season_by_id
from nonebot_plugin_mahjong_scoreboard.service.season_user_point_service import get_season_user_point_rank, \
    count_season_user_point
from nonebot_plugin_mahjong_scoreboard.service.user_service import get_user_by_binding_qq

# ========== 查询PT ==========
query_season_point_matcher = on_command("查询PT", aliases={"查询pt", "PT", "pt"}, priority=5)

require_parse_unary_at_arg(query_season_point_matcher, "user_binding_qq")
require_group_binding_qq(query_season_point_matcher)
require_user_binding_qq(query_season_point_matcher)
require_running_season(query_season_point_matcher)


@query_season_point_matcher.handle()
@general_interceptor(query_season_point_matcher)
async def query_season_point(matcher: Matcher):
    user = await get_user_by_binding_qq(matcher.state["user_binding_qq"])

    season = await get_season_by_id(matcher.state["running_season_id"])
    sup = await season_user_point_service.get_season_user_point(season, user)
    if sup is None:
        raise BadRequestError("你还没有参加过对局")

    rank = await get_season_user_point_rank(sup)
    total = await count_season_user_point(season)

    msg = await map_season_user_point(sup, rank, total)
    await matcher.send(msg)


# ========== 查询榜单 ==========
query_season_ranking_matcher = on_command("查询榜单", aliases={"榜单"}, priority=5)

require_parse_unary_text_arg(query_season_ranking_matcher, "season_code")
require_group_binding_qq(query_season_ranking_matcher)


@query_season_ranking_matcher.handle()
@general_interceptor(query_season_ranking_matcher)
async def query_season_ranking(bot: Bot, event: MessageEvent, matcher: Matcher):
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

    sups = await season_user_point_service.get_season_user_points(season)

    msgs = await map_season_user_points(group, season, sups)
    await send_msgs(bot, event, msgs)
