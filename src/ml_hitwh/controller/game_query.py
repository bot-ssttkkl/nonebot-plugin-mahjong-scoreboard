from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.internal.matcher import Matcher

from ml_hitwh.controller.interceptor import general_interceptor
from ml_hitwh.controller.mapper.game_mapper import map_user_recent_games_as_forward_msg, \
    map_group_recent_games_as_forward_msg, map_user_uncompleted_games_as_forward_msg, \
    map_group_uncompleted_games_as_forward_msg
from ml_hitwh.controller.utils import split_message
from ml_hitwh.service.game_service import get_user_games, get_group_games
from ml_hitwh.service.group_service import get_group_by_binding_qq
from ml_hitwh.service.user_service import get_user_by_binding_qq

# ========== 个人最近对局 ==========
query_user_recent_games_matcher = on_command("个人最近对局", aliases={"最近对局"}, priority=5)


@query_user_recent_games_matcher.handle()
@general_interceptor(query_user_recent_games_matcher)
async def query_user_recent_games(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    user_id = event.user_id

    args = split_message(event.message)
    if len(args) > 1 and args[1].type == 'at':
        user_id = int(args[1].data["qq"])

    group = await get_group_by_binding_qq(event.group_id)
    user = await get_user_by_binding_qq(user_id)

    games = await get_user_games(group, user, limit=30, reverse_order=True)
    if len(games) != 0:
        msg = await map_user_recent_games_as_forward_msg(games, group, user)
        await bot.send_group_forward_msg(group_id=event.group_id, messages=msg)
    else:
        await matcher.send("你还没有进行过对局")


# ========== 群最近对局 ==========
query_group_recent_games_matcher = on_command("群最近对局", priority=5)


@query_group_recent_games_matcher.handle()
@general_interceptor(query_group_recent_games_matcher)
async def query_group_recent_games(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    group = await get_group_by_binding_qq(event.group_id)

    games = await get_group_games(group, limit=30, reverse_order=True)
    if len(games) != 0:
        msg = await map_group_recent_games_as_forward_msg(games)
        await bot.send_group_forward_msg(group_id=event.group_id, messages=msg)
    else:
        await matcher.send("本群还没有进行过对局")


# ========== 个人未完成对局 ==========
query_user_uncompleted_games_matcher = on_command("个人未完成对局", aliases={"未完成对局"}, priority=5)


@query_group_recent_games_matcher.handle()
@general_interceptor(query_group_recent_games_matcher)
async def query_group_recent_games(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    user_id = event.user_id

    args = split_message(event.message)
    if len(args) > 1 and args[1].type == 'at':
        user_id = int(args[1].data["qq"])

    group = await get_group_by_binding_qq(event.group_id)
    user = await get_user_by_binding_qq(user_id)

    games = await get_user_games(group, user, True, limit=30, reverse_order=True)
    if len(games) != 0:
        msg = await map_user_uncompleted_games_as_forward_msg(games, group, user)
        await bot.send_group_forward_msg(group_id=event.group_id, messages=msg)
    else:
        await matcher.send("你还没有未完成的对局")


# ========== 群未完成对局 ==========
query_group_recent_games_matcher = on_command("群未完成对局", priority=5)


@query_group_recent_games_matcher.handle()
@general_interceptor(query_group_recent_games_matcher)
async def query_group_recent_games(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    group = await get_group_by_binding_qq(event.group_id)

    games = await get_group_games(group, True, limit=30, reverse_order=True)
    if len(games) != 0:
        msg = await map_group_uncompleted_games_as_forward_msg(games)
        await bot.send_group_forward_msg(group_id=event.group_id, messages=msg)
    else:
        await matcher.send("本群还没有未完成的对局")
