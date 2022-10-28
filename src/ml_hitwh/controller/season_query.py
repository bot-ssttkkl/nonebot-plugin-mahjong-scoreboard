from nonebot import on_command
from nonebot.internal.matcher import Matcher

from ml_hitwh.controller.interceptor import general_interceptor
from ml_hitwh.controller.mapper.season_mapper import map_season
from ml_hitwh.controller.general_handlers import require_group_binding_qq, require_unary_text
from ml_hitwh.errors import BadRequestError
from ml_hitwh.service import season_service
from ml_hitwh.service.group_service import get_group_by_binding_qq

# ========== 赛季信息 ==========
query_running_season_matcher = on_command("查询赛季", aliases={"赛季"}, priority=5)

require_unary_text(query_running_season_matcher, "season_code",
                   decorator=general_interceptor(query_running_season_matcher))
require_group_binding_qq(query_running_season_matcher)


@query_running_season_matcher.handle()
@general_interceptor(query_running_season_matcher)
async def query_running_season_handle(matcher: Matcher):
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
