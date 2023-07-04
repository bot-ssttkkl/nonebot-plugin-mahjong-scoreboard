from io import StringIO

from mahjong_scoreboard_model import Season, User, SeasonUserPoint
from nonebot import Bot
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher, current_bot

from .interceptor import handle_error
from .mapper import season_state_mapping, map_point
from .mapper.pagination_mapper import map_pagination
from .mapper.season_user_point_mapper import map_season_user_point
from .mg import matcher_group
from .utils.dep import RunningSeasonDep, UserDep, SeasonFromUnaryArgOrRunningSeason
from .utils.general_handlers import require_store_command_args, require_platform_group_id, require_platform_user_id
from ..errors import ResultError
from ..platform.get_user_nickname import get_user_nickname
from ..platform.send_messages import send_msgs
from ..service.season_user_point_service import get_season_user_point, get_season_user_points
from ..utils.nonebot import default_cmd_start

# ========== 查询PT ==========
query_season_point_matcher = matcher_group.on_command("查询PT", aliases={"查询pt", "PT", "pt"}, priority=5)
query_season_point_matcher.__help_info__ = f"{default_cmd_start}查询PT [@<用户>]"

require_store_command_args(query_season_point_matcher)
require_platform_group_id(query_season_point_matcher)
require_platform_user_id(query_season_point_matcher)


@query_season_point_matcher.handle()
@handle_error()
async def query_season_point(matcher: Matcher, season: Season = RunningSeasonDep(),
                             user: User = UserDep()):
    sup = await get_season_user_point(season.id, user.id)
    if sup is None:
        raise ResultError("用户还没有参加过对局")

    msg = await map_season_user_point(sup, season)
    await matcher.send(msg)


# ========== 查询榜单 ==========
query_season_ranking_matcher = matcher_group.on_command("查询榜单", aliases={"榜单"}, priority=5)
query_season_ranking_matcher.__help_info__ = f"{default_cmd_start}查询榜单 [<赛季代号>]"

require_store_command_args(query_season_ranking_matcher)
require_platform_group_id(query_season_ranking_matcher)


async def map_sup(sup: SeasonUserPoint, season: Season):
    bot = current_bot.get()
    line = f"#{sup.rank}  " \
           f"{await get_user_nickname(bot, sup.user.platform_user_id, season.group.platform_group_id)}    " \
           f"{map_point(sup.point, season.config.point_precision)}"
    return line


@query_season_ranking_matcher.handle()
@handle_error()
async def query_season_ranking(bot: Bot, event: Event,
                               season: Season = SeasonFromUnaryArgOrRunningSeason()):
    sups = await get_season_user_points(season.id)

    msgs = await map_pagination(sups, lambda x: map_sup(x, season))

    # 赛季：[赛季名]
    # 状态：进行中
    with StringIO() as sio:
        sio.write(f"赛季：{season.name}\n"
                  f"状态：{season_state_mapping[season.state]}")
        if len(sups) == 0:
            sio.write("还没有用户参与该赛季")

        msgs.insert(0, sio.getvalue().strip())

    await send_msgs(bot, event, msgs)
