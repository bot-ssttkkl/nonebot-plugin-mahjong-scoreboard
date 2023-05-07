# ========== 查询最近走势 ==========
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.internal.matcher import Matcher

from nonebot_plugin_mahjong_scoreboard.controller.general_handlers import require_parse_unary_at_arg, \
    require_group_binding_qq, require_user_binding_qq, require_running_season
from nonebot_plugin_mahjong_scoreboard.controller.interceptor import general_interceptor
from nonebot_plugin_mahjong_scoreboard.controller.mapper.game_statistics_mapper import map_season_user_trend, \
    map_game_statistics
from nonebot_plugin_mahjong_scoreboard.controller.utils.message import SplitCommandArgs
from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.service import season_user_point_service
from nonebot_plugin_mahjong_scoreboard.service.game_service import get_game_statistics
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_group_by_binding_qq
from nonebot_plugin_mahjong_scoreboard.service.season_service import get_season_by_id, get_season_by_code
from nonebot_plugin_mahjong_scoreboard.service.user_service import get_user_by_binding_qq

# ============ 查询最近走势 ============
query_season_user_trend_matcher = on_command("查询最近走势", aliases={"最近走势", "走势"}, priority=5)

require_parse_unary_at_arg(query_season_user_trend_matcher, "user_binding_qq")
require_group_binding_qq(query_season_user_trend_matcher)
require_user_binding_qq(query_season_user_trend_matcher)
require_running_season(query_season_user_trend_matcher)


@query_season_user_trend_matcher.handle()
@general_interceptor(query_season_user_trend_matcher)
async def query_season_user_trend(matcher: Matcher):
    group_binding_qq = matcher.state["binding_qq"]
    user_binding_qq = matcher.state["user_binding_qq"]

    group = await get_group_by_binding_qq(group_binding_qq)
    user = await get_user_by_binding_qq(user_binding_qq)

    season = await get_season_by_id(matcher.state["running_season_id"])
    logs = await season_user_point_service.get_season_user_point_change_logs(season, user,
                                                                             limit=10, reverse_order=True,
                                                                             join_game_and_record=True)
    if len(logs) != 0:
        msg = await map_season_user_trend(group, user, season, logs)
        await matcher.send(msg)
    else:
        raise BadRequestError("你还没有参加过对局")


# ============ 对战数据 ============
query_user_statistics_matcher = on_command("对战数据", priority=5)

require_parse_unary_at_arg(query_user_statistics_matcher, "user_binding_qq")
require_group_binding_qq(query_user_statistics_matcher)
require_user_binding_qq(query_user_statistics_matcher)


@query_user_statistics_matcher.handle()
@general_interceptor(query_user_statistics_matcher)
async def query_user_statistics(matcher: Matcher):
    group_binding_qq = matcher.state["binding_qq"]
    user_binding_qq = matcher.state["user_binding_qq"]

    group = await get_group_by_binding_qq(group_binding_qq)
    user = await get_user_by_binding_qq(user_binding_qq)

    game_statistics = await get_game_statistics(group, user)
    msg = await map_game_statistics(group, user, None, game_statistics)
    await matcher.send(msg)


# ============ 赛季对战数据 ============
query_season_user_statistics_matcher = on_command("赛季对战数据", priority=5)


@query_season_user_statistics_matcher.handle()
@general_interceptor(query_season_user_statistics_matcher)
async def parse_query_season_user_statistics_args(matcher: Matcher, args: Message = SplitCommandArgs()):
    user_id = None
    season_code = None

    for arg in args:
        if arg.type == "at":
            user_id = int(arg.data["qq"])
        elif arg.type == "text":
            season_code = arg.data["text"]

    if user_id is not None:
        matcher.state["user_binding_qq"] = user_id

    if season_code is not None:
        matcher.state["season_code"] = season_code


require_parse_unary_at_arg(query_season_user_statistics_matcher, "user_binding_qq")
require_group_binding_qq(query_season_user_statistics_matcher)
require_user_binding_qq(query_season_user_statistics_matcher)


@query_season_user_statistics_matcher.handle()
@general_interceptor(query_season_user_statistics_matcher)
async def query_season_user_statistics(matcher: Matcher):
    group_binding_qq = matcher.state["binding_qq"]
    user_binding_qq = matcher.state["user_binding_qq"]

    group = await get_group_by_binding_qq(group_binding_qq)
    user = await get_user_by_binding_qq(user_binding_qq)

    season_code = matcher.state.get("season_code", None)
    if season_code:
        season = await get_season_by_code(season_code, group)
        if season is None:
            raise BadRequestError("找不到指定赛季")
    else:
        if group.running_season_id:
            season = await get_season_by_id(group.running_season_id)
        else:
            raise BadRequestError("当前没有运行中的赛季")

    game_statistics = await get_game_statistics(group, user, season)
    msg = await map_game_statistics(group, user, season, game_statistics)
    await matcher.send(msg)
