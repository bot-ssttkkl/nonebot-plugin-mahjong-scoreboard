import re
from io import StringIO
from typing import Type

from cachetools import TTLCache
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.internal.matcher import Matcher

from nonebot_plugin_mahjong_scoreboard.controller.context import save_context, get_context
from nonebot_plugin_mahjong_scoreboard.controller.general_handlers import require_parse_unary_text_arg, \
    require_game_code_from_context, require_parse_unary_integer_arg
from nonebot_plugin_mahjong_scoreboard.controller.interceptor import general_interceptor
from nonebot_plugin_mahjong_scoreboard.controller.mapper.game_mapper import map_game
from nonebot_plugin_mahjong_scoreboard.controller.utils import split_message, parse_int_or_error, try_parse_wind
from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.model.enums import PlayerAndWind, GameState
from nonebot_plugin_mahjong_scoreboard.service import game_service, group_service, user_service
from nonebot_plugin_mahjong_scoreboard.utils.onebot import default_cmd_start

group_latest_game_code = TTLCache(4096, 7200)


def require_game_code_from_context_and_group_latest_game_code(matcher_type: Type[Matcher]):
    @matcher_type.handle()
    @general_interceptor(matcher_type)
    async def prepare(event: GroupMessageEvent, matcher: Matcher):
        context = get_context(event)
        if context and "game_code" in context:
            matcher.state["game_code"] = context["game_code"]
        elif event.group_id in group_latest_game_code:
            matcher.state["game_code"] = group_latest_game_code[event.group_id]

    return matcher_type


# =============== 新建对局 ===============
new_game_matcher = on_command("新建对局", aliases={"新对局"}, priority=5)

require_parse_unary_text_arg(new_game_matcher, "player_and_wind")


@new_game_matcher.handle()
@general_interceptor(new_game_matcher)
async def new_game(event: GroupMessageEvent, matcher: Matcher):
    player_and_wind = matcher.state.get("player_and_wind", None)

    if player_and_wind == "四人东":
        player_and_wind = PlayerAndWind.four_men_east
    elif player_and_wind == "四人南":
        player_and_wind = PlayerAndWind.four_men_south
    elif player_and_wind is not None:
        raise BadRequestError("对局类型不合法")

    user = await user_service.get_user_by_binding_qq(event.user_id)
    group = await group_service.get_group_by_binding_qq(event.group_id)
    game = await game_service.new_game(user, group, player_and_wind)

    msg = await map_game(game)
    msg.append(MessageSegment.text(f'\n\n新建对局成功，对此消息回复“{default_cmd_start}结算 <成绩>”指令记录你的成绩'))
    send_result = await matcher.send(msg)

    save_context(send_result["message_id"], game_code=game.code)
    group_latest_game_code[event.group_id] = game.code


# =============== 结算 ===============
record_matcher = on_command("结算对局", aliases={"结算"}, priority=5)

require_game_code_from_context_and_group_latest_game_code(record_matcher)


@record_matcher.handle()
@general_interceptor(record_matcher)
async def parse_record_args(event: GroupMessageEvent, matcher: Matcher):
    game_code = matcher.state.get("game_code")
    user_id = event.user_id
    score = None
    wind = None

    args = split_message(event.message)[1:]

    for arg in args:
        if arg.type == "text":
            text = arg.data["text"]
            if text.startswith("对局"):
                game_code = text[len("对局"):]
                game_code = parse_int_or_error(game_code, "对局编号")
            elif text.endswith("风"):
                wind = try_parse_wind(text[:len("风")])
            elif text.endswith("家"):
                wind = try_parse_wind(text[:len("家")])
            else:
                pending_wind = try_parse_wind(text)
                if pending_wind is not None:
                    wind = pending_wind
                else:
                    score = text
        elif arg.type == 'at':
            user_id = int(arg.data["qq"])

    score = parse_int_or_error(score, '成绩')

    if game_code is None:
        raise BadRequestError("请指定对局编号")

    matcher.state["game_code"] = game_code
    matcher.state["user_binding_qq"] = user_id
    matcher.state["score"] = score
    matcher.state["wind"] = wind


@record_matcher.handle()
@general_interceptor(record_matcher)
async def record(event: GroupMessageEvent, matcher: Matcher):
    user = await user_service.get_user_by_binding_qq(matcher.state["user_binding_qq"])
    group = await group_service.get_group_by_binding_qq(event.group_id)
    operator = await user_service.get_user_by_binding_qq(event.user_id)

    game = await game_service.record_game(matcher.state["game_code"], group, user,
                                          matcher.state["score"], matcher.state["wind"], operator)

    msg = await map_game(game)
    msg.append(MessageSegment.text('\n\n结算成功'))
    if game.state == GameState.invalid_total_point:
        msg.append(MessageSegment.text(f"\n警告：对局的成绩之和不正确，对此消息回复“{default_cmd_start}结算 <成绩>”指令重新记录你的成绩"))
    send_result = await matcher.send(msg)
    save_context(send_result["message_id"], game_code=game.code)


# =============== 撤销结算 ===============
revert_record_matcher = on_command("撤销结算对局", aliases={"撤销结算"}, priority=5)

require_game_code_from_context_and_group_latest_game_code(revert_record_matcher)


@revert_record_matcher.handle()
@general_interceptor(revert_record_matcher)
async def parse_revert_record_args(event: GroupMessageEvent, matcher: Matcher):
    game_code = matcher.state.get("game_code")
    user_id = event.user_id

    args = split_message(event.message)[1:]

    for arg in args:
        if arg.type == "text":
            text = arg.data["text"]
            if text.startswith("对局"):
                game_code = parse_int_or_error(text[len("对局"):], '对局编号')
        elif arg.type == 'at':
            user_id = int(arg.data["qq"])

    if game_code is None:
        raise BadRequestError("请指定对局编号")

    matcher.state["game_code"] = game_code
    matcher.state["user_binding_qq"] = user_id


@revert_record_matcher.handle()
@general_interceptor(revert_record_matcher)
async def revert_record(event: GroupMessageEvent, matcher: Matcher):
    user = await user_service.get_user_by_binding_qq(matcher.state["user_binding_qq"])
    operator = await user_service.get_user_by_binding_qq(event.user_id)
    group = await group_service.get_group_by_binding_qq(event.group_id)
    game = await game_service.revert_record(matcher.state["game_code"], group, user, operator)

    msg = await map_game(game)
    msg.append(MessageSegment.text('\n\n撤销结算成功'))
    send_result = await matcher.send(msg)
    save_context(send_result["message_id"], game_code=game.code)


# =============== 设置对局PT ===============
set_record_point_matcher = on_command("设置对局PT", aliases={"对局PT"}, priority=5)

require_game_code_from_context_and_group_latest_game_code(set_record_point_matcher)


@set_record_point_matcher.handle()
@general_interceptor(set_record_point_matcher)
async def parse_record_point_args(event: GroupMessageEvent, matcher: Matcher):
    game_code = matcher.state.get("game_code")
    user_id = event.user_id
    point = None

    args = split_message(event.message)[1:]

    for arg in args:
        if arg.type == "text":
            text = arg.data["text"]
            if text.startswith("对局"):
                game_code = parse_int_or_error(text[len("对局"):], '对局编号')
            else:
                point = text
        elif arg.type == 'at':
            user_id = int(arg.data["qq"])

    point = parse_int_or_error(point, 'PT')

    if game_code is None:
        raise BadRequestError("请指定对局编号")

    matcher.state["game_code"] = game_code
    matcher.state["user_binding_qq"] = user_id
    matcher.state["point"] = point


@set_record_point_matcher.handle()
@general_interceptor(set_record_point_matcher)
async def set_record_point(event: GroupMessageEvent, matcher: Matcher):
    user = await user_service.get_user_by_binding_qq(matcher.state["user_binding_qq"])
    group = await group_service.get_group_by_binding_qq(event.group_id)
    operator = await user_service.get_user_by_binding_qq(event.user_id)

    game = await game_service.set_record_point(matcher.state["game_code"], group, user,
                                               matcher.state["point"], operator)

    msg = await map_game(game)
    msg.append(MessageSegment.text('\n\n设置PT成功'))
    send_result = await matcher.send(msg)
    save_context(send_result["message_id"], game_code=game.code)


# =============== 删除对局 ===============
delete_game_matcher = on_command("删除对局", priority=5)

require_game_code_from_context(delete_game_matcher)  # 删除对局必须指定编号
require_parse_unary_integer_arg(delete_game_matcher, "game_code")


@delete_game_matcher.handle()
@general_interceptor(delete_game_matcher)
async def delete_game(event: GroupMessageEvent, matcher: Matcher):
    game_code = matcher.state.get("game_code", None)

    if game_code is None:
        raise BadRequestError("请指定对局编号")

    group = await group_service.get_group_by_binding_qq(event.group_id)
    operator = await user_service.get_user_by_binding_qq(event.user_id)
    await game_service.delete_game(game_code, group, operator)

    await matcher.send(f'成功删除对局{game_code}')


# =============== 设置对局进度 ===============
make_game_progress_matcher = on_command("设置对局进度", aliases={"对局进度"}, priority=5)

require_game_code_from_context_and_group_latest_game_code(make_game_progress_matcher)

round_honba_pattern = r"([东南])([一二三四1234])局([0123456789零一两二三四五六七八九十百千万亿]+)本场"


@make_game_progress_matcher.handle()
@general_interceptor(make_game_progress_matcher)
async def parse_make_game_progress_args(event: GroupMessageEvent, matcher: Matcher):
    game_code = matcher.state.get("game_code")
    completed = False
    round = None
    honba = None

    args = split_message(event.message)[1:]

    for arg in args:
        if arg.type == 'text':
            text = arg.data["text"]
            if text.startswith("对局"):
                game_code = parse_int_or_error(text[len("对局"):], '对局编号')
            elif text == '完成':
                completed = True
            else:
                match_result = re.match(round_honba_pattern, text)
                if match_result is not None:
                    wind, round, honba = match_result.groups()

                    round = parse_int_or_error(round, "局数", True)
                    if wind == '南':
                        round *= 2

                    honba = parse_int_or_error(honba, "本场", True)

    if game_code is None:
        raise BadRequestError("请指定对局编号")

    matcher.state["game_code"] = game_code
    matcher.state["completed"] = completed
    matcher.state["round"] = round
    matcher.state["honba"] = honba


@make_game_progress_matcher.handle()
@general_interceptor(make_game_progress_matcher)
async def make_game_progress(event: GroupMessageEvent, matcher: Matcher):
    group = await group_service.get_group_by_binding_qq(event.group_id)
    operator = await user_service.get_user_by_binding_qq(event.user_id)
    if not matcher.state["completed"]:
        game = await game_service.make_game_progress(matcher.state["game_code"],
                                                     matcher.state["round"],
                                                     matcher.state["honba"],
                                                     group, operator)
    else:
        game = await game_service.remove_game_progress(matcher.state["game_code"], group)

    msg = await map_game(game)
    msg.append(MessageSegment.text("\n\n成功设置对局进度"))
    send_result = await matcher.send(msg)
    save_context(send_result["message_id"], game_code=game.code)


# ========== 设置对局备注 ===========
set_game_comment_matcher = on_command("设置对局备注", aliases={"对局备注"}, priority=5)

require_game_code_from_context_and_group_latest_game_code(set_game_comment_matcher)


@set_game_comment_matcher.handle()
@general_interceptor(set_game_comment_matcher)
async def parse_set_game_comment_args(event: GroupMessageEvent, matcher: Matcher):
    game_code = matcher.state.get("game_code")
    comment = StringIO()

    args = split_message(event.message, False)[1:]
    for arg in args:
        if arg.type == 'text':
            text = arg.data["text"]
            if game_code is None and text.startswith("对局"):
                game_code = parse_int_or_error(text[len("对局"):], '对局编号')
            else:
                comment.write(text)
                comment.write(" ")

    comment = comment.getvalue()
    if not comment:
        raise BadRequestError("请输入备注")

    if game_code is None:
        raise BadRequestError("请指定对局编号")

    matcher.state["game_code"] = game_code
    matcher.state["comment"] = comment


@set_game_comment_matcher.handle()
@general_interceptor(set_game_comment_matcher)
async def set_game_comment(event: GroupMessageEvent, matcher: Matcher):
    group = await group_service.get_group_by_binding_qq(event.group_id)
    operator = await user_service.get_user_by_binding_qq(event.user_id)
    game = await game_service.set_game_comment(matcher.state["game_code"], group, matcher.state["comment"], operator)

    msg = await map_game(game)
    msg.append(MessageSegment.text("\n\n成功设置对局备注"))
    send_result = await matcher.send(msg)
    save_context(send_result["message_id"], game_code=game.code)
