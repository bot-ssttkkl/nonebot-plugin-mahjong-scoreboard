from asyncio import Lock
from typing import Optional, Callable

from mahjong_scoreboard_model import Group
from nonebot import Bot
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import Depends
from nonebot.params import CommandArg
from nonebot_plugin_session import extract_session

from .message import split_message
from ..interceptor import handle_error
from ...errors import BadRequestError, ResultError
from ...platform.mention import extract_mention_user
from ...service.group_service import get_group, is_group_admin
from ...service.season_service import get_group_running_season, get_season_by_code
from ...service.user_service import get_user
from ...utils.session import get_platform_group_id, get_platform_user_id


def SplitCommandArgs(*, lookup_matcher_state: bool = True,
                     lookup_matcher_state_key: Optional[str] = "command_args_store",
                     ignore_empty: bool = True):
    def dep(matcher: Matcher, command_arg=CommandArg()):
        if lookup_matcher_state and command_arg is None:
            command_arg = matcher.state.get(lookup_matcher_state_key)
        if command_arg is not None:
            return split_message(command_arg, ignore_empty)
        else:
            return []

    return Depends(dep)


def SessionDep():
    def dependency(bot: Bot, event: Event):
        session = extract_session(bot, event)
        return session

    return Depends(dependency)


def GroupDep(*, lookup_matcher_state: bool = True,
             lookup_matcher_state_key: str = "platform_group_id",
             raise_on_missing: bool = True):
    @handle_error()
    async def dependency(matcher: Matcher, session=SessionDep()):
        platform_group_id = None
        if lookup_matcher_state:
            platform_group_id = matcher.state.get(lookup_matcher_state_key)
        if platform_group_id is None:
            platform_group_id = get_platform_group_id(session)

        if platform_group_id is None:
            if raise_on_missing:
                raise BadRequestError("该指令仅限群聊环境中使用")
            else:
                return None

        return await get_group(platform_group_id)

    return Depends(dependency)


def UserDep(*, lookup_matcher_state: bool = True,
            lookup_matcher_state_key: str = "platform_user_id",
            use_mention_user_arg: bool = True,
            mention_user_arg_lookup_matcher_state: bool = True,
            mention_user_arg_lookup_matcher_state_key: str = "command_args_store",
            use_sender: bool = True,
            raise_on_missing: bool = True):
    # 优先级：消息中的提及、matcher.state、事件发送者
    @handle_error()
    async def dependency(matcher: Matcher, session=SessionDep(),
                         mention=MentionUserArg(lookup_matcher_state=mention_user_arg_lookup_matcher_state,
                                                lookup_matcher_state_key=mention_user_arg_lookup_matcher_state_key)):
        platform_user_id = None
        if use_mention_user_arg and mention is not None:
            platform_user_id = mention
        if platform_user_id is None and lookup_matcher_state:
            platform_user_id = matcher.state.get(lookup_matcher_state_key)
        if platform_user_id is None and use_sender:
            platform_user_id = get_platform_user_id(session)

        if platform_user_id is None:
            if raise_on_missing:
                raise BadRequestError("请指定用户")
            else:
                return None

        if "db_mutex" not in matcher.state:
            matcher.state["db_mutex"] = Lock()
        async with matcher.state["db_mutex"]:
            return await get_user(platform_user_id)

    return Depends(dependency)


def SenderUserDep():
    return UserDep(lookup_matcher_state=False, use_mention_user_arg=False)


def RunningSeasonDep(*, group_lookup_matcher_state: bool = True,
                     group_lookup_matcher_state_key: str = "platform_group_id",
                     raise_on_missing: bool = True):
    @handle_error()
    async def dependency(matcher: Matcher, group=GroupDep(lookup_matcher_state=group_lookup_matcher_state,
                                                          lookup_matcher_state_key=group_lookup_matcher_state_key)):
        if "db_mutex" not in matcher.state:
            matcher.state["db_mutex"] = Lock()
        async with matcher.state["db_mutex"]:
            season = await get_group_running_season(group.id)
            if season is None and raise_on_missing:
                raise ResultError("当前没有运行中的赛季")
            return season

    return Depends(dependency)


def UnaryArg(*, lookup_matcher_state: bool = True,
             lookup_matcher_state_key: str = "command_args_store",
             parser: Optional[Callable[[str], any]] = None):
    @handle_error()
    async def dependency(args=SplitCommandArgs(lookup_matcher_state=lookup_matcher_state,
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


def MentionUserArg(*, lookup_matcher_state: bool = True,
                   lookup_matcher_state_key: str = "command_args_store"):
    def dependency(args=SplitCommandArgs(lookup_matcher_state=lookup_matcher_state,
                                         lookup_matcher_state_key=lookup_matcher_state_key)):
        for arg in args:
            x = extract_mention_user(arg)
            if x is not None:
                return x

        return None

    return Depends(dependency)


def SeasonFromUnaryArgOrRunningSeason(*, unary_arg_lookup_matcher_state: bool = True,
                                      unary_arg_lookup_matcher_state_key: str = "command_args_store"):
    @handle_error()
    async def dependency(matcher: Matcher, group: Group = GroupDep(),
                         season_code=UnaryArg(lookup_matcher_state=unary_arg_lookup_matcher_state,
                                              lookup_matcher_state_key=unary_arg_lookup_matcher_state_key)):
        if "db_mutex" not in matcher.state:
            matcher.state["db_mutex"] = Lock()
        async with matcher.state["db_mutex"]:
            if season_code:
                season = await get_season_by_code(season_code, group.id)
                if season is None:
                    raise ResultError("找不到指定赛季")
            else:
                season = await get_group_running_season(group.id)
                if season is None:
                    raise ResultError("当前没有运行中的赛季")
            return season

    return Depends(dependency)


def IsGroupAdminDep(raise_on_false: bool = True):
    @handle_error()
    async def dependency(group=GroupDep(), sender=SenderUserDep()):
        admin = await is_group_admin(sender.id, group.id)
        if not admin and raise_on_false:
            raise ResultError("权限不足")
        return admin

    return dependency
