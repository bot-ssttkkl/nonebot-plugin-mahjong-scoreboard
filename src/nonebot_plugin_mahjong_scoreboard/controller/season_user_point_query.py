from io import StringIO

from nonebot import on_command, Bot
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher

from .interceptor import handle_error
from .mapper import season_state_mapping, map_point
from .mapper.season_user_point_mapper import map_season_user_point
from .utils.dep import RunningSeasonDep, UserDep, SeasonFromUnaryArgOrRunningSeason
from .utils.general_handlers import require_store_command_args, require_platform_group_id, require_platform_user_id
from ..errors import BadRequestError
from ..model import Season, User
from ..platform.get_user_nickname import get_user_nickname
from ..platform.send_messages import send_msgs
from ..service.season_user_point_service import get_season_user_point, get_season_user_points

# ========== 查询PT ==========
query_season_point_matcher = on_command("查询PT", aliases={"查询pt", "PT", "pt"}, priority=5)

require_store_command_args(query_season_point_matcher)
require_platform_group_id(query_season_point_matcher)
require_platform_user_id(query_season_point_matcher)


@query_season_point_matcher.handle()
@handle_error()
async def query_season_point(matcher: Matcher, season: Season = RunningSeasonDep(),
                             user: User = UserDep()):
    sup = await get_season_user_point(season.id, user.id)
    if sup is None:
        raise BadRequestError("你还没有参加过对局")

    msg = await map_season_user_point(sup, season)
    await matcher.send(msg)


# ========== 查询榜单 ==========
query_season_ranking_matcher = on_command("查询榜单", aliases={"榜单"}, priority=5)

require_store_command_args(query_season_ranking_matcher)
require_platform_group_id(query_season_ranking_matcher)

RECORD_PER_MSG = 10


@query_season_ranking_matcher.handle()
@handle_error()
async def query_season_ranking(bot: Bot, event: Event,
                               season: Season = SeasonFromUnaryArgOrRunningSeason()):
    sups = await get_season_user_points(season.id)

    msgs = []

    pending = 0
    pending_msg_io = StringIO()

    # 赛季：[赛季名]
    # 状态：进行中
    pending_msg_io.write(f"赛季：{season.name}\n")
    pending_msg_io.write(f"状态：{season_state_mapping[season.state]}\n\n")

    if len(sups) == 0:
        pending_msg_io.write("还没有用户参与该赛季")
        msgs.append(pending_msg_io.getvalue().strip())
    else:
        for sup in sups:
            line = f"#{sup.rank}  " \
                   f"{await get_user_nickname(bot, sup.user.platform_user_id, season.group.platform_group_id)}    " \
                   f"{map_point(sup.point, season.config.point_precision)}\n"
            pending_msg_io.write(line)
            pending += 1

            if 0 < RECORD_PER_MSG <= pending:
                msgs.append(pending_msg_io.getvalue().strip())
                pending = 0
                pending_msg_io = StringIO()

        if pending > 0:
            msgs.append(pending_msg_io.getvalue().strip())

    await send_msgs(bot, event, msgs)
