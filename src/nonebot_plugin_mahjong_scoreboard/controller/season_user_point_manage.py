from nonebot import Bot
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from nonebot_plugin_session import Session

from .interceptor import handle_error
from .mapper.season_user_point_mapper import map_season_user_point
from .mg import matcher_group
from .utils.dep import UserDep, GroupDep, RunningSeasonDep, SessionDep, UnaryArg, SenderUserDep, IsGroupAdminDep
from .utils.general_handlers import require_store_command_args, require_platform_group_id, require_platform_user_id
from .utils.parse import parse_float_or_error
from ..model import Group, User, Season
from ..platform.get_user_nickname import get_user_nickname
from ..service.season_user_point_service import reset_season_user_point, change_season_user_point_manually
from ..utils.nonebot import default_cmd_start
from ..model.platform_id import get_platform_group_id

# ========== 设置用户PT ==========
set_season_user_point_matcher = matcher_group.on_command("设置用户PT", aliases={"设置用户pt", "设置PT", "设置pt"}, priority=5)
set_season_user_point_matcher.__help_info__ = f"{default_cmd_start}设置PT <PT> [@<用户>]"

require_store_command_args(set_season_user_point_matcher)
require_platform_group_id(set_season_user_point_matcher)
require_platform_user_id(set_season_user_point_matcher, use_sender_on_group_message=False)


@set_season_user_point_matcher.handle()
@handle_error()
async def set_season_user_point_confirm(bot: Bot, matcher: Matcher, session: Session = SessionDep(),
                                        user: User = UserDep(use_sender=False),
                                        pt=UnaryArg(parser=lambda x: parse_float_or_error(x, 'PT')),
                                        group_admin=IsGroupAdminDep()):
    await matcher.pause(
        f"确定设置用户[{await get_user_nickname(bot, user.platform_user_id, get_platform_group_id(session))}]"
        f"PT为{pt}吗？(y/n)")


@set_season_user_point_matcher.handle()
@handle_error()
async def set_season_user_point_end(event: Event, matcher: Matcher,
                                    group: Group = GroupDep(),
                                    user: User = UserDep(use_sender=False),
                                    operator: User = SenderUserDep(),
                                    season: Season = RunningSeasonDep(),
                                    pt=UnaryArg(parser=lambda x: parse_float_or_error(x, 'PT'))):
    if event.get_message().extract_plain_text() == 'y':
        sup = await change_season_user_point_manually(season.id,
                                                      group.id, user.id,
                                                      pt,
                                                      operator.id)
        msg = await map_season_user_point(sup, season)
        msg += "\n\n设置用户PT成功"
        await matcher.send(msg)
    else:
        await matcher.finish("取消设置用户PT")


# ========== 重置用户PT ==========
reset_season_user_point_matcher = matcher_group.on_command("重置用户PT", aliases={"重置用户pt", "重置PT", "重置pt"}, priority=5)
reset_season_user_point_matcher.__help_info__ = f"{default_cmd_start}重置PT [@<用户>]"

require_store_command_args(reset_season_user_point_matcher)
require_platform_group_id(reset_season_user_point_matcher)
require_platform_user_id(reset_season_user_point_matcher, use_sender_on_group_message=False)


@reset_season_user_point_matcher.handle()
@handle_error()
async def reset_season_user_point_confirm(bot: Bot, matcher: Matcher, session: Session = SessionDep(),
                                          user: User = UserDep(use_sender=False),
                                          group_admin=IsGroupAdminDep()):
    await matcher.pause(
        f"确定重置用户[{await get_user_nickname(bot, user.platform_user_id, get_platform_group_id(session))}]"
        f"PT吗？(y/n)")


@reset_season_user_point_matcher.handle()
@handle_error()
async def reset_season_user_point_end(event: Event, matcher: Matcher,
                                      group: Group = GroupDep(),
                                      user: User = UserDep(use_sender=False),
                                      operator: User = SenderUserDep(),
                                      season: Season = RunningSeasonDep()):
    if event.get_message().extract_plain_text() == 'y':
        await reset_season_user_point(season.id,
                                      group.id, user.id,
                                      operator.id)
        await matcher.send("重置用户PT成功")
    else:
        await matcher.finish("取消重置用户PT")
