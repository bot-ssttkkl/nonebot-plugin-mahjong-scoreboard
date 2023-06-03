# ========== 查询最近走势 ==========
from io import StringIO

from nonebot import Bot
from nonebot.internal.matcher import Matcher, current_bot
from nonebot_plugin_session import Session

from .interceptor import handle_error
from .mapper import map_point, digit_mapping, percentile_str, map_real_point
from .mg import matcher_group
from .utils.dep import GroupDep, SessionDep, RunningSeasonDep, UserDep, SeasonFromUnaryArgOrRunningSeason
from .utils.general_handlers import require_store_command_args, require_platform_group_id, require_platform_user_id
from ..errors import ResultError
from ..model import GameStatistics, Group, Season, User
from ..platform.get_user_nickname import get_user_nickname
from ..service.game_service import get_game_statistics, get_games, get_season_game_statistics
from ..utils.nonebot import default_cmd_start
from ..utils.session import get_platform_group_id

# ============ 查询最近走势 ============
query_season_user_trend_matcher = matcher_group.on_command("最近走势", aliases={"走势"}, priority=5)
query_season_user_trend_matcher.__help_info__ = f"{default_cmd_start}最近走势 [@<用户>]"

require_store_command_args(query_season_user_trend_matcher)
require_platform_group_id(query_season_user_trend_matcher)
require_platform_user_id(query_season_user_trend_matcher)


@query_season_user_trend_matcher.handle()
@handle_error()
async def query_season_user_trend(bot: Bot, matcher: Matcher, group: Group = GroupDep(),
                                  session: Session = SessionDep(),
                                  user: User = UserDep(),
                                  season: Season = RunningSeasonDep()):
    games = await get_games(group.id, user.id, season.id, limit=10, reverse_order=True, completed_only=True)

    if games.total != 0:
        with StringIO() as sio:
            sio.write(f"用户[{await get_user_nickname(bot, user.platform_user_id, get_platform_group_id(session))}]"
                      f"的最近走势如下：\n")

            for game in games.data:
                record = game.records[0]
                for r in game.records:
                    if r.user.id == user.id:
                        record = r

                sio.write(f"  {record.rank}位    {record.score}点  "
                          f"({map_point(record.raw_point, record.point_scale)})  "
                          f"对局{game.code}\n")

            await matcher.send(sio.getvalue().strip())
    else:
        raise ResultError("用户还没有参加过对局")


# ============ 对战数据 ============
async def map_game_statistics(game_statistics: GameStatistics, user: User, group: Group) -> str:
    bot = current_bot.get()
    with StringIO() as sio:
        sio.write(f"用户[{await get_user_nickname(bot, user.platform_user_id, group.platform_group_id)}]的对战数据：\n")

        sio.write(f"  对局数：{game_statistics.total} （半庄：{game_statistics.total_south}、东风：{game_statistics.total_east}）\n")
        for i, rate in enumerate(game_statistics.rates):
            sio.write(f"  {digit_mapping[i + 1]}位率：{percentile_str(rate)}\n")
        sio.write(f"  平均顺位：{round(game_statistics.avg_rank, 2)}\n")
        if game_statistics.pt_expectation is not None:
            sio.write(f"  PT期望：{map_real_point(game_statistics.pt_expectation, 2)}\n")
        sio.write(f"  被飞率：{percentile_str(game_statistics.flying_rate)}")

        return sio.getvalue().strip()


query_user_statistics_matcher = matcher_group.on_command("对战数据", priority=5)
query_user_statistics_matcher.__help_info__ = f"{default_cmd_start}对战数据 [@<用户>]"

require_store_command_args(query_user_statistics_matcher)
require_platform_group_id(query_user_statistics_matcher)
require_platform_user_id(query_user_statistics_matcher)


@query_user_statistics_matcher.handle()
@handle_error()
async def query_user_statistics(matcher: Matcher, group: Group = GroupDep(),
                                user: User = UserDep()):
    game_statistics = await get_game_statistics(group.id, user.id)
    msg = await map_game_statistics(game_statistics, user, group)
    await matcher.send(msg)


# ============ 赛季对战数据 ============
query_season_user_statistics_matcher = matcher_group.on_command("赛季对战数据", priority=5)
query_season_user_statistics_matcher.__help_info__ = f"{default_cmd_start}赛季对战数据 [<赛季代号>] [@<用户>]"

require_store_command_args(query_season_user_statistics_matcher)
require_platform_group_id(query_season_user_statistics_matcher)
require_platform_user_id(query_season_user_statistics_matcher)


@query_season_user_statistics_matcher.handle()
@handle_error()
async def query_season_user_statistics(matcher: Matcher, group: Group = GroupDep(),
                                       user: User = UserDep(),
                                       season: Season = SeasonFromUnaryArgOrRunningSeason()):
    game_statistics = await get_season_game_statistics(group.id, user.id, season.id)
    msg = await  map_game_statistics(game_statistics, user, group)
    await matcher.send(msg)
