import time
from collections import OrderedDict
from io import StringIO
from typing import Union

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot
from pydantic import BaseModel

from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.orm.game import PlayerAndWind
from ml_hitwh.service import game_record_service
from .utils import split_message
from .utils.interceptor import handle_error
from .utils.mapper import map_game
from ..model.enums import GameState

CONTEXT_TTL = 7200


class GameRecordMessageContext(BaseModel):
    message_id: int
    game_code: int
    expires_at: float = time.time() + CONTEXT_TTL
    extra: dict = {}


context_data = OrderedDict()


# 弹出过期的context
def collate_context():
    now = time.time()
    while len(context_data) > 0:
        front = next(iter(context_data.values()))
        if front.expires_at <= now:
            context_data.popitem()
        else:
            break


async def get_context(event: GroupMessageEvent):
    collate_context()

    message_id = None
    for seg in event.original_message:
        if seg.type == "reply":
            message_id = int(seg.data["id"])
            break

    if message_id:
        return context_data.get(message_id, None)


async def save_context(game_code: int, message_id: int, **kwargs):
    collate_context()

    context = GameRecordMessageContext(game_code=game_code, message_id=message_id, extra=kwargs)
    if message_id in context_data:
        del context_data[message_id]
    context_data[message_id] = context


# 用户新建对局
new_game_matcher = on_command("新建对局", priority=5)


@new_game_matcher.handle()
@handle_error(new_game_matcher)
async def new_game(bot: Bot, event: GroupMessageEvent):
    player_and_wind = PlayerAndWind.four_men_south

    args = split_message(event.message)
    if len(args) > 1:
        game_type = str(args[1])
        if game_type == "四人东":
            player_and_wind = PlayerAndWind.four_men_east
        elif game_type == "四人南":
            player_and_wind = PlayerAndWind.four_men_south
        else:
            raise BadRequestError("对局类型不合法")

    game = await game_record_service.new_game(event.user_id, event.group_id, player_and_wind)

    with StringIO() as sio:
        await map_game(sio, game, bot, event)
        sio.write('\n')
        sio.write('新建对局成功，对此消息回复“/结算 <成绩>”指令记录你的成绩')
        msg = sio.getvalue()

    send_result = await new_game_matcher.send(msg)
    await save_context(game_code=game['code'], message_id=send_result["message_id"])


# =============== 结算 ===============
record_matcher = on_command("结算", priority=5)


@record_matcher.handle()
@handle_error(record_matcher)
async def record(bot: Bot, event: GroupMessageEvent):
    user_id = event.user_id
    game_code = None
    score = None

    context = await get_context(event)
    if context:
        game_code = context.game_code

    args = split_message(event.message)

    if len(args) <= 1:
        raise BadRequestError("指令格式不合法")

    if args[1].type == "text":
        if args[1].data["text"].startswith("对局"):
            # 以下两种格式：
            # 结算 对局<编号> <成绩>
            # 结算 对局<编号> @<用户> <成绩>
            game_code = args[1].data["text"][len("对局"):]

            if args[2].type == "text":
                # 结算 对局<编号> <成绩>
                score = args[2].data["text"]
            elif args[2].type == "at":
                # 结算 对局<编号> @<用户> <成绩>
                user_id = int(args[2].data["qq"])
                score = args[3].data["text"]
            else:
                raise BadRequestError("指令格式不合法")
        else:
            # 结算 <成绩>
            score = args[1].data["text"]
    elif args[1].type == "at":
        # 结算 @<用户> <成绩>
        user_id = int(args[1].data["qq"])
        score = args[2].data["text"]
    else:
        raise BadRequestError("指令格式不合法")

    game_code = parse_int_or_error(game_code, '对局编号')
    score = parse_int_or_error(game_code, '成绩')

    game = await game_record_service.record_game(game_code, event.group_id, event.user_id, score)

    with StringIO() as sio:
        await map_game(sio, game, bot, event)
        sio.write('\n')
        if game['state'] == GameState.uncompleted:
            sio.write('记录成功')
        elif game['state'] == GameState.invalid_total_point:
            sio.write("警告：对局的成绩之和不正确，对此消息回复“/结算 <成绩>”指令重新记录你的成绩")
        msg = sio.getvalue()

    send_result = await record_matcher.send(msg)
    await save_context(game_code=game['code'], message_id=send_result["message_id"], user_id=user_id)


#
#
# # =============== 撤销结算 ===============
# revert_record_matcher = on_command("撤销结算", priority=5)
#
#
# @revert_record_matcher.handle()
# @handle_error(revert_record_matcher)
# async def revert_record(bot: Bot, event: GroupMessageEvent):
#     user_id = event.user_id
#     game_code = None
#
#     context = await get_context(event)
#     if context:
#         user_id = context.extra.get("user_id", None)
#         game_code = context.game_code
#
#     args = split_message(event.message)
#
#     if len(args) > 1:
#         if args[1].type == "text":
#             if args[1].data["text"].startswith("对局"):
#                 # 以下两种格式：
#                 # 撤销结算 对局<编号>
#                 # 撤销结算 对局<编号> @<用户>
#                 game_code = args[1].data["text"][len("对局"):]
#
#                 if len(args) > 2 and args[2].type == "at":
#                     # 撤销结算 对局<编号> @<用户>
#                     user_id = args[2].data["qq"]
#                 # else:
#                 # 撤销结算 对局<编号>
#         else:
#             # 撤销结算 @<用户>
#             user_id = int(args[1].data["qq"])
#     # else:
#     # 撤销结算
#
#     game_code = parse_int_or_error(game_code, '对局编号')
#
#     game = await game_client.revert_record(sender=build_sender_params(bot, event),
#                                            code=game_code,
#                                            user_binding_qq=user_id)
#
#     with StringIO() as sio:
#         await map_game(sio, game, bot, event)
#         sio.write('\n')
#         sio.write('撤销结算成功')
#         msg = sio.getvalue()
#
#     send_result = await record_matcher.send(msg)
#     await save_context(game_code=game['code'], message_id=send_result["message_id"], user_id=user_id)
#
#
# # =============== 设置对局PT ===============
# set_point_matcher = on_command("设置对局PT", aliases={"设置对局分数"}, priority=5)
#
#
# @set_point_matcher.handle()
# @handle_error(set_point_matcher)
# async def set_point(bot: Bot, event: GroupMessageEvent):
#     user_id = event.user_id
#     game_code = None
#     point = None
#
#     context = await get_context(event)
#     if context:
#         game_code = context.game_code
#
#     args = split_message(event.message)
#
#     if len(args) <= 1:
#         raise BadRequestError("指令格式不合法")
#
#     if args[1].type == "text":
#         if args[1].data["text"].startswith("对局"):
#             # 以下两种格式：
#             # 设置PT 对局<编号> <PT>
#             # 设置PT 对局<编号> @<用户> <PT>
#             game_code = args[1].data["text"][len("对局"):]
#
#             if args[2].type == "text":
#                 # 设置PT 对局<编号> <PT>
#                 point = args[2].data["text"]
#             elif args[2].type == "at":
#                 # 设置PT 对局<编号> @<用户> <PT>
#                 user_id = int(args[2].data["qq"])
#                 point = args[3].data["text"]
#             else:
#                 raise BadRequestError("指令格式不合法")
#         else:
#             # 设置PT <PT>
#             point = args[1].data["text"]
#     elif args[1].type == "at":
#         # 设置PT @<用户> <PT>
#         user_id = int(args[1].data["qq"])
#         point = args[2].data["text"]
#     else:
#         raise BadRequestError("指令格式不合法")
#
#     game_code = parse_int_or_error(game_code, '对局编号')
#     point = parse_int_or_error(game_code, 'PT')
#
#     game = await game_client.set_point(sender=build_sender_params(bot, event),
#                                        code=game_code,
#                                        user_binding_qq=user_id,
#                                        point=point)
#
#     with StringIO() as sio:
#         await map_game(sio, game, bot, event)
#         sio.write('\n')
#         sio.write('设置对局PT成功')
#
#         msg = sio.getvalue()
#
#     send_result = await record_matcher.send(msg)
#     await save_context(game_code=game['code'], message_id=send_result["message_id"], user_id=user_id)
#
#
# # =============== 查询对局 ===============
# query_by_code_matcher = on_command("查询对局", priority=5)
#
#
# @query_by_code_matcher.handle()
# @handle_error(query_by_code_matcher)
# async def query_by_code(bot: Bot, event: GroupMessageEvent):
#     game_code = None
#
#     context = await get_context(event)
#     if context:
#         game_code = context.game_code
#
#     args = split_message(event.message)
#     if len(args) >= 2 and args[1].type == 'text':
#         game_code = args[1].data["text"]
#
#     game_code = parse_int_or_error(game_code, '对局编号')
#
#     game = await game_client.query_by_code(sender=build_sender_params(bot, event),
#                                            code=game_code)
#
#     with StringIO() as sio:
#         await map_game(sio, game, bot, event, map_sponsor=True)
#         msg = sio.getvalue()
#
#     send_result = await query_by_code_matcher.send(msg)
#     await save_context(game_code=game['code'], message_id=send_result["message_id"])
#
#
# # =============== 删除对局 ===============
# delete_game_matcher = on_command("删除对局", priority=5)
#
#
# @delete_game_matcher.handle()
# @handle_error(delete_game_matcher)
# async def delete_game(bot: Bot, event: GroupMessageEvent):
#     game_code = None
#
#     context = await get_context(event)
#     if context:
#         game_code = context.game_code
#
#     args = split_message(event.message)
#     if len(args) >= 2:
#         game_code = int(args[1].data["text"])
#
#     game_code = parse_int_or_error(game_code, '对局编号')
#
#     await game_client.delete(sender=build_sender_params(bot, event),
#                              code=game_code)
#
#     await query_by_code_matcher.send(f'成功删除对局{game_code}')
#
#
def parse_int_or_error(raw: Union[int, str, None], desc: str) -> int:
    if not raw:
        raise BadRequestError(f"请指定{desc}")

    try:
        return int(raw)
    except ValueError:
        raise BadRequestError(f"{desc}不合法")
