# ========== 查询最近走势 ==========
from nonebot import on_command
from nonebot.internal.matcher import Matcher

from nonebot_plugin_mahjong_scoreboard.controller.general_handlers import require_parse_unary_at_arg, \
    require_group_binding_qq, require_user_binding_qq
from nonebot_plugin_mahjong_scoreboard.controller.interceptor import general_interceptor
from nonebot_plugin_mahjong_scoreboard.controller.mapper.season_user_point_mapper import map_season_user_trend
from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.service import season_user_point_service
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_group_by_binding_qq
from nonebot_plugin_mahjong_scoreboard.service.season_service import get_season_by_id
from nonebot_plugin_mahjong_scoreboard.service.user_service import get_user_by_binding_qq

query_season_user_trend_matcher = on_command("查询最近走势", aliases={"最近走势", "走势"}, priority=5)

require_parse_unary_at_arg(query_season_user_trend_matcher, "user_binding_qq")
require_group_binding_qq(query_season_user_trend_matcher)
require_user_binding_qq(query_season_user_trend_matcher)


@query_season_user_trend_matcher.handle()
@general_interceptor(query_season_user_trend_matcher)
async def query_season_user_trend(matcher: Matcher):
    group_binding_qq = matcher.state["binding_qq"]
    user_binding_qq = matcher.state["user_binding_qq"]

    group = await get_group_by_binding_qq(group_binding_qq)
    user = await get_user_by_binding_qq(user_binding_qq)

    if group.running_season_id is not None:
        season = await get_season_by_id(group.running_season_id)
        logs = await season_user_point_service.get_season_user_point_change_logs(season, user,
                                                                                 limit=10, reverse_order=True,
                                                                                 join_game_and_record=True)
        if len(logs) != 0:
            msg = await map_season_user_trend(group, user, season, logs)
            await matcher.send(msg)
        else:
            raise BadRequestError("你还没有参加过对局")
    else:
        raise BadRequestError("当前没有运行中的赛季")
