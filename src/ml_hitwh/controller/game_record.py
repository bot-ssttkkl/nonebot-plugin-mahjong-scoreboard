import re
from io import StringIO

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.internal.matcher import Matcher

from ml_hitwh.controller.context import save_context, get_context
from ml_hitwh.controller.general_handlers import require_unary_text
from ml_hitwh.controller.interceptor import general_interceptor
from ml_hitwh.controller.mapper.game_mapper import map_game
from ml_hitwh.controller.utils import split_message, parse_int_or_error, try_parse_wind
from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.enums import PlayerAndWind, GameState
from ml_hitwh.service import game_service, group_service, user_service

# =============== 新建对局 ===============
new_game_matcher = on_command("新建对局", aliases={"新对局"}, priority=5)

require_unary_text(new_game_matcher, "player_and_wind",
                   decorator=general_interceptor(new_game_matcher))


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
    msg.append(MessageSegment.text('\n\n新建对局成功，对此消息回复“/结算 <成绩>”指令记录你的成绩'))
    send_result = await matcher.send(msg)
    save_context(send_result["message_id"], game_code=game.code)


# =============== 结算 ===============
record_matcher = on_command("结算对局", aliases={"结算"}, priority=5)


@record_matcher.handle()
@general_interceptor(record_matcher)
async def record(event: GroupMessageEvent, matcher: Matcher):
    user_id = event.user_id
    game_code = None
    score = None
    wind = None

    context = get_context(event)
    if context:
        game_code = context["game_code"]

    args = split_message(event.message)[1:]

    for arg in args:
        if arg.type == "text":
            text = arg.data["text"]
            if text.startswith("对局"):
                game_code = text[len("对局"):]
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

    game_code = parse_int_or_error(game_code, '对局编号')
    score = parse_int_or_error(score, '成绩')

    user = await user_service.get_user_by_binding_qq(user_id)
    group = await group_service.get_group_by_binding_qq(event.group_id)

    game = await game_service.get_game_by_code(game_code, group)
    if game is None:
        raise BadRequestError("未找到指定对局")

    game = await game_service.record_game(game, user, score, wind)

    msg = await map_game(game)
    msg.append(MessageSegment.text('\n\n结算成功'))
    if game.state == GameState.invalid_total_point:
        msg.append(MessageSegment.text("\n警告：对局的成绩之和不正确，对此消息回复“/结算 <成绩>”指令重新记录你的成绩"))
    send_result = await matcher.send(msg)
    save_context(send_result["message_id"], game_code=game.code, user_id=user_id)


# =============== 撤销结算 ===============
revert_record_matcher = on_command("撤销结算对局", aliases={"撤销结算"}, priority=5)


@revert_record_matcher.handle()
@general_interceptor(revert_record_matcher)
async def revert_record(event: GroupMessageEvent, matcher: Matcher):
    user_id = event.user_id
    game_code = None

    context = get_context(event)
    if context:
        user_id = context.get("user_id", None)
        game_code = context["game_code"]

    args = split_message(event.message)[1:]

    for arg in args:
        if arg.type == "text":
            text = arg.data["text"]
            if text.startswith("对局"):
                game_code = text[len("对局"):]
        elif arg.type == 'at':
            user_id = int(arg.data["qq"])

    game_code = parse_int_or_error(game_code, '对局编号')

    user = await user_service.get_user_by_binding_qq(user_id)
    operator = await user_service.get_user_by_binding_qq(event.user_id)
    group = await group_service.get_group_by_binding_qq(event.group_id)
    game = await game_service.revert_record(game_code, group, user, operator)

    msg = await map_game(game)
    msg.append(MessageSegment.text('\n\n撤销结算成功'))
    send_result = await matcher.send(msg)
    save_context(send_result["message_id"], game_code=game.code, user_id=user_id)


# =============== 设置对局PT ===============
set_record_point_matcher = on_command("设置对局PT", aliases={"对局PT"}, priority=5)


@set_record_point_matcher.handle()
@general_interceptor(set_record_point_matcher)
async def set_record_point(event: GroupMessageEvent, matcher: Matcher):
    user_id = event.user_id
    game_code = None
    point = None

    context = get_context(event)
    if context:
        game_code = context["game_code"]

    args = split_message(event.message)[1:]

    for arg in args:
        if arg.type == "text":
            text = arg.data["text"]
            if text.startswith("对局"):
                game_code = text[len("对局"):]
            else:
                point = text
        elif arg.type == 'at':
            user_id = int(arg.data["qq"])

    game_code = parse_int_or_error(game_code, '对局编号')
    point = parse_int_or_error(point, 'PT')

    user = await user_service.get_user_by_binding_qq(user_id)
    group = await group_service.get_group_by_binding_qq(event.group_id)
    operator = await user_service.get_user_by_binding_qq(event.user_id)

    game = await game_service.set_record_point(game_code, group, user, point, operator)

    msg = await map_game(game)
    msg.append(MessageSegment.text('\n\n设置PT成功'))
    send_result = await matcher.send(msg)
    save_context(send_result["message_id"], game_code=game.code, user_id=user_id)


# =============== 删除对局 ===============
delete_game_matcher = on_command("删除对局", priority=5)

require_unary_text(delete_game_matcher, "game_code",
                   decorator=general_interceptor(delete_game_matcher))


@delete_game_matcher.handle()
@general_interceptor(delete_game_matcher)
async def delete_game(event: GroupMessageEvent, matcher: Matcher):
    game_code = None

    context = get_context(event)
    if context:
        game_code = context["game_code"]

    game_code = matcher.state.get("game_code", game_code)

    game_code = parse_int_or_error(game_code, '对局编号')

    group = await group_service.get_group_by_binding_qq(event.group_id)
    operator = await user_service.get_user_by_binding_qq(event.user_id)
    await game_service.delete_game(game_code, group, operator)

    await matcher.send(f'成功删除对局{game_code}')


# =============== 设置对局进度 ===============
make_game_progress_matcher = on_command("设置对局进度", aliases={"对局进度"}, priority=5)

round_honba_pattern = r"([东南])([一二三四1234])局([0123456789零一两二三四五六七八九十百千万亿]+)本场"


@make_game_progress_matcher.handle()
@general_interceptor(make_game_progress_matcher)
async def make_game_progress(event: GroupMessageEvent, matcher: Matcher):
    game_code = None
    completed = False
    round = None
    honba = None

    context = get_context(event)
    if context:
        game_code = context["game_code"]

    args = split_message(event.message)[1:]
    for arg in args:
        if arg.type == 'text':
            text = arg.data["text"]
            if text.startswith("对局"):
                game_code = text[len("对局"):]
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

    game_code = parse_int_or_error(game_code, '对局编号')

    group = await group_service.get_group_by_binding_qq(event.group_id)
    operator = await user_service.get_user_by_binding_qq(event.user_id)
    if not completed:
        game = await game_service.make_game_progress(game_code, round, honba, group, operator)
    else:
        game = await game_service.remove_game_progress(game_code, group)

    msg = await map_game(game)
    msg.append(MessageSegment.text("\n\n成功设置对局进度"))
    send_result = await matcher.send(msg)
    save_context(send_result["message_id"], game_code=game.code)


# ========== 设置对局备注 ===========
set_game_comment_matcher = on_command("设置对局备注", aliases={"对局备注"}, priority=5)


@set_game_comment_matcher.handle()
@general_interceptor(set_game_comment_matcher)
async def set_game_comment(event: GroupMessageEvent, matcher: Matcher):
    game_code = None
    comment = StringIO()

    context = get_context(event)
    if context:
        game_code = context["game_code"]

    args = split_message(event.message, False)[1:]
    for arg in args:
        if arg.type == 'text':
            text = arg.data["text"]
            if game_code is None and text.startswith("对局"):
                game_code = text[len("对局"):]
            else:
                comment.write(text)
                comment.write(" ")

    game_code = parse_int_or_error(game_code, '对局编号')

    comment = comment.getvalue()
    if not comment:
        raise BadRequestError("请输入备注")

    group = await group_service.get_group_by_binding_qq(event.group_id)
    game = await game_service.set_game_comment(game_code, group, comment)

    msg = await map_game(game)
    msg.append(MessageSegment.text("\n\n成功设置对局备注"))
    send_result = await matcher.send(msg)
    save_context(send_result["message_id"], game_code=game.code)
