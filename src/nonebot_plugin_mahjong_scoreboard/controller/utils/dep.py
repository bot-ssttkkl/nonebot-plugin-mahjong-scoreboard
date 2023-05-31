from asyncio import Lock
from typing import Optional, Callable

from nonebot import Bot
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import Depends
from nonebot_plugin_session import extract_session

from .message import SplitCommandArgs
from ..interceptor import handle_error
from ...errors import BadRequestError
from ...model import Group
from ...platform.mention import extract_mention_user
from ...service.group_service import get_group
from ...service.season_service import get_group_running_season, get_season_by_code
from ...service.user_service import get_user
from ...utils.session import get_platform_group_id, get_platform_user_id


def SessionDep():
    def dependency(bot: Bot, event: Event):
        session = extract_session(bot, event)
        return session

    return Depends(dependency)


def GroupDep(*, lookup_matcher_state: bool = True,
             lookup_matcher_state_key: Optional[str] = "platform_group_id",
             raise_on_private_message: bool = True):
    @handle_error()
    async def dependency(matcher: Matcher, session=SessionDep()):
        platform_group_id = None
        if lookup_matcher_state:
            platform_group_id = matcher.state.get(lookup_matcher_state_key)
        if platform_group_id is None:
            platform_group_id = get_platform_group_id(session)

        if platform_group_id is None and raise_on_private_message:
            raise BadRequestError("该指令仅限群聊环境中使用")

        if "db_mutex" not in matcher.state:
            matcher.state["db_mutex"] = Lock()
        async with matcher.state["db_mutex"]:
            return await get_group(platform_group_id)

    return Depends(dependency)


def UserDep(*, lookup_matcher_state: bool = True,
            lookup_matcher_state_key: Optional[str] = None):
    async def dependency(matcher: Matcher, session=SessionDep()):
        platform_user_id = None
        if lookup_matcher_state:
            platform_user_id = matcher.state.get(lookup_matcher_state_key)
        if platform_user_id is None:
            platform_user_id = get_platform_user_id(session)

        if "db_mutex" not in matcher.state:
            matcher.state["db_mutex"] = Lock()
        async with matcher.state["db_mutex"]:
            return await get_user(platform_user_id)

    return Depends(dependency)


def RunningSeasonDep(*, lookup_matcher_state: bool = True,
                     lookup_matcher_state_key: Optional[str] = "platform_group_id",
                     raise_on_missing: bool = True):
    @handle_error()
    async def dependency(matcher: Matcher, group=GroupDep(lookup_matcher_state=lookup_matcher_state,
                                                          lookup_matcher_state_key=lookup_matcher_state_key)):
        if "db_mutex" not in matcher.state:
            matcher.state["db_mutex"] = Lock()
        async with matcher.state["db_mutex"]:
            season = await get_group_running_season(group.id)
            if season is None and raise_on_missing:
                raise BadRequestError("当前没有运行中的赛季")
            return season

    return Depends(dependency)


def UnaryArg(*, lookup_matcher_state: bool = False,
             lookup_matcher_state_key: Optional[str] = "command_args_store",
             parser: Optional[Callable[[str], any]] = None):
    def dependency(args=SplitCommandArgs(lookup_matcher_state=lookup_matcher_state,
                                         lookup_matcher_state_key=lookup_matcher_state_key)):
        x = None

        for arg in args:
            if arg.type == "text":
                x = arg.data["text"]
                break

        if x is not None:
            if parser is not None:
                x = parser(x)
        return x

    return Depends(dependency)


def MentionUserArg(*, lookup_matcher_state: bool = False,
                   lookup_matcher_state_key: Optional[str] = "command_args_store"):
    def dependency(args=SplitCommandArgs(lookup_matcher_state=lookup_matcher_state,
                                         lookup_matcher_state_key=lookup_matcher_state_key)):
        for arg in args:
            x = extract_mention_user(arg)
            if x is not None:
                return x

        return None

    return Depends(dependency)


def SeasonFromUnaryArgOrRunningSeason():
    @handle_error()
    async def dependency(matcher: Matcher, group: Group = GroupDep(),
                         season_code=UnaryArg(lookup_matcher_state=True)):
        if "db_mutex" not in matcher.state:
            matcher.state["db_mutex"] = Lock()
        async with matcher.state["db_mutex"]:
            if season_code:
                season = await get_season_by_code(season_code, group.id)
                if season is None:
                    raise BadRequestError("找不到指定赛季")
            else:
                season = await get_group_running_season(group.id)
                if season is None:
                    raise BadRequestError("当前没有运行中的赛季")
            return season

    return Depends(dependency)
