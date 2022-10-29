from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.internal.matcher import Matcher

from nonebot_plugin_mahjong_scoreboard.controller.general_handlers import require_group_binding_qq, \
    require_user_binding_qq
from nonebot_plugin_mahjong_scoreboard.controller.interceptor import general_interceptor
from nonebot_plugin_mahjong_scoreboard.controller.mapper.season_user_point_mapper import map_season_user_point, \
    map_season_user_points
from nonebot_plugin_mahjong_scoreboard.controller.season_user_point_manage import set_season_user_point_matcher
from nonebot_plugin_mahjong_scoreboard.controller.utils import send_group_forward_msg, send_private_forward_msg
from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.service import season_user_point_service
from nonebot_plugin_mahjong_scoreboard.service.group_service import get_group_by_binding_qq
from nonebot_plugin_mahjong_scoreboard.service.season_service import get_season_by_id
from nonebot_plugin_mahjong_scoreboard.service.season_user_point_service import get_season_user_point_rank, \
    count_season_user_point
from nonebot_plugin_mahjong_scoreboard.service.user_service import get_user_by_binding_qq

# ========== 查询PT ==========
query_season_point = on_command("查询PT", aliases={"查询pt", "PT", "pt"}, priority=5)

require_group_binding_qq(query_season_point)
require_user_binding_qq(query_season_point)


@query_season_point.handle()
@general_interceptor(query_season_point)
async def query_season_point(matcher: Matcher):
    group_binding_qq = matcher.state["binding_qq"]
    user_binding_qq = matcher.state["user_binding_qq"]

    group = await get_group_by_binding_qq(group_binding_qq)
    user = await get_user_by_binding_qq(user_binding_qq)

    if group.running_season_id is not None:
        season = await get_season_by_id(group.running_season_id)
        sup = await season_user_point_service.get_season_user_point(season, user)
        if sup is None:
            raise BadRequestError("你还没有参加过对局")

        rank = await get_season_user_point_rank(sup)
        total = await count_season_user_point(season)

        msg = await map_season_user_point(sup, rank, total)
        await matcher.send(msg)
    else:
        raise BadRequestError("当前没有运行中的赛季")


# ========== 查询榜单 ==========
query_season_ranking = on_command("查询榜单", aliases={"榜单"}, priority=5)

require_group_binding_qq(query_season_ranking)


@query_season_ranking.handle()
@general_interceptor(query_season_ranking)
async def query_season_ranking(bot: Bot, event: MessageEvent, matcher: Matcher):
    group_binding_qq = matcher.state["binding_qq"]

    group = await get_group_by_binding_qq(group_binding_qq)

    if group.running_season_id is not None:
        season = await get_season_by_id(group.running_season_id)
        sups = await season_user_point_service.get_season_user_points(season)

        msgs = await map_season_user_points(season, sups)
        if len(msgs) == 1:
            await matcher.send(msgs[0])
        else:
            if isinstance(event, GroupMessageEvent):
                await send_group_forward_msg(bot, event.group_id, msgs)
            else:
                await send_private_forward_msg(bot, event.user_id, msgs)
    else:
        raise BadRequestError("当前没有运行中的赛季")
