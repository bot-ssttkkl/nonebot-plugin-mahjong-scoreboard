from datetime import date, timedelta, datetime, time

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.internal.matcher import Matcher

from ml_hitwh.controller.context import get_context, save_context
from ml_hitwh.controller.general_handlers import require_unary_at, require_unary_text
from ml_hitwh.controller.interceptor import general_interceptor
from ml_hitwh.controller.mapper.game_mapper import map_game
from ml_hitwh.controller.utils import send_group_forward_msg, parse_int_or_error
from ml_hitwh.errors import BadRequestError
from ml_hitwh.service import group_service, game_service
from ml_hitwh.service.game_service import get_user_games, get_group_games
from ml_hitwh.service.group_service import get_group_by_binding_qq
from ml_hitwh.service.user_service import get_user_by_binding_qq

# =============== 查询对局 ===============
query_by_code_matcher = on_command("查询对局", aliases={"对局"}, priority=5)

require_unary_text(query_by_code_matcher, "game_code",
                   decorator=general_interceptor(query_by_code_matcher))


@query_by_code_matcher.handle()
@general_interceptor(query_by_code_matcher)
async def query_by_code(event: GroupMessageEvent, matcher: Matcher):
    game_code = None

    context = get_context(event)
    if context:
        game_code = context["game_code"]

    game_code = matcher.state.get("game_code", game_code)

    game_code = parse_int_or_error(game_code, '对局编号')

    group = await group_service.get_group_by_binding_qq(event.group_id)
    game = await game_service.get_game_by_code(game_code, group)
    if game is None:
        raise BadRequestError("未找到指定对局")

    msg = await map_game(game)
    send_result = await matcher.send(msg)
    save_context(send_result["message_id"], game_code=game.code)


# ========== 个人最近对局 ==========
query_user_recent_games_matcher = on_command("个人最近对局", aliases={"最近对局"}, priority=5)

require_unary_at(query_user_recent_games_matcher, "user_id",
                 decorator=general_interceptor(query_user_recent_games_matcher))


@query_user_recent_games_matcher.handle()
@general_interceptor(query_user_recent_games_matcher)
async def query_user_recent_games(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    user_id = matcher.state.get("user_id", event.user_id)

    group = await get_group_by_binding_qq(event.group_id)
    user = await get_user_by_binding_qq(user_id)

    end_time = datetime.combine(date.today() + timedelta(days=1), time())
    start_time = datetime.combine(end_time - timedelta(days=7), time())

    games = await get_user_games(group, user, limit=30, reverse_order=True, time_span=(start_time, end_time))
    if len(games) != 0:
        member_info = await bot.get_group_member_info(group_id=group.binding_qq, user_id=user.binding_qq)
        header = Message([
            MessageSegment.text("以下是"),
            MessageSegment("at", {"qq": user.binding_qq, "name": member_info["nickname"]}),
            MessageSegment.text("的最近对局")
        ])
        messages = [header]
        for g in games:
            messages.append(await map_game(g, map_promoter=True))
        await send_group_forward_msg(bot, event.group_id, messages)
    else:
        await matcher.send("你还没有进行过对局")


# ========== 群最近对局 ==========
query_group_recent_games_matcher = on_command("群最近对局", priority=5)


@query_group_recent_games_matcher.handle()
@general_interceptor(query_group_recent_games_matcher)
async def query_group_recent_games(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    group = await get_group_by_binding_qq(event.group_id)

    end_time = datetime.combine(date.today() + timedelta(days=1), time())
    start_time = datetime.combine(end_time - timedelta(days=7), time())

    games = await get_group_games(group, limit=30, reverse_order=True, time_span=(start_time, end_time))
    if len(games) != 0:
        header = Message(MessageSegment.text("以下是本群的最近对局"))
        messages = [header]
        for g in games:
            messages.append(await map_game(g, map_promoter=True))
        await send_group_forward_msg(bot, event.group_id, messages)
    else:
        await matcher.send("本群还没有进行过对局")


# ========== 个人未完成对局 ==========
query_user_uncompleted_games_matcher = on_command("个人未完成对局", aliases={"未完成对局"}, priority=5)

require_unary_at(query_user_uncompleted_games_matcher, "user_id",
                 decorator=general_interceptor(query_user_uncompleted_games_matcher))


@query_user_uncompleted_games_matcher.handle()
@general_interceptor(query_group_recent_games_matcher)
async def query_user_uncompleted_games(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    user_id = matcher.state.get("user_id", event.user_id)

    group = await get_group_by_binding_qq(event.group_id)
    user = await get_user_by_binding_qq(user_id)

    games = await get_user_games(group, user, uncompleted_only=True, limit=30, reverse_order=True)
    if len(games) != 0:
        member_info = await bot.get_group_member_info(group_id=group.binding_qq, user_id=user.binding_qq)
        header = Message([
            MessageSegment.text("以下是"),
            MessageSegment("at", {"qq": user.binding_qq, "name": member_info["nickname"]}),
            MessageSegment.text("的未完成对局")
        ])

        messages = [header]
        for g in games:
            messages.append(await map_game(g, map_promoter=True))
        await send_group_forward_msg(bot, event.group_id, messages)
    else:
        await matcher.send("你还没有未完成的对局")


# ========== 群未完成对局 ==========
query_group_uncompleted_games_matcher = on_command("群未完成对局", priority=5)


@query_group_uncompleted_games_matcher.handle()
@general_interceptor(query_group_uncompleted_games_matcher)
async def query_group_uncompleted_games(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    group = await get_group_by_binding_qq(event.group_id)

    games = await get_group_games(group, uncompleted_only=True, limit=30, reverse_order=True)
    if len(games) != 0:
        header = Message(MessageSegment.text("以下是本群的未完成对局"))
        messages = [header]
        for g in games:
            messages.append(await map_game(g, map_promoter=True))
        await send_group_forward_msg(bot, event.group_id, messages)
    else:
        await matcher.send("本群还没有未完成的对局")
