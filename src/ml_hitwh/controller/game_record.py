from io import StringIO

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot

from ml_hitwh.errors import BadRequestError
from ml_hitwh.model.game import GameState, Game
from ml_hitwh.model.game_record_message_context import GameRecordMessageContext
from ml_hitwh.service import game_record
from .utils import split_message, get_user_name


async def get_context(event: GroupMessageEvent):
    message_id = None
    for seg in event.original_message:
        if seg.type == "reply":
            message_id = int(seg.data["id"])
            break

    if message_id:
        return await GameRecordMessageContext.find_one(GameRecordMessageContext.message_id == message_id)


async def save_context(game_id: int, message_id: int, **kwargs):
    context = GameRecordMessageContext(game_id=game_id, message_id=message_id, extra=kwargs)
    await context.insert()


async def build_game_record_text(game: Game, bot: Bot, event: GroupMessageEvent):
    with StringIO() as sb:
        for i, r in enumerate(sorted(game.record, key=lambda r: r.point, reverse=True)):
            name = await get_user_name(r.user_id, event.group_id, bot)
            sb.write(f"#{i + 1}  {name}\t{str(r.point).rjust(6)}\n")
        return sb.getvalue()


# 用户新建对局
new_game_matcher = on_command("新建对局", priority=5)


@new_game_matcher.handle()
async def new_game(event: GroupMessageEvent):
    game = await game_record.new_game(event.user_id, event.group_id)
    send_result = await new_game_matcher.send(f"成功新建对局{game.game_id}，对此消息回复“结算 <分数>”指令记录你的分数")

    await save_context(game_id=game.game_id, message_id=send_result["message_id"])


# 计数用
record_matcher = on_command("结算", priority=5)


@record_matcher.handle()
async def record(bot: Bot, event: GroupMessageEvent):
    try:
        user_id = event.user_id
        game_id = None
        point = None

        context = await get_context(event)
        if context:
            game_id = context.game_id

        args = split_message(event.message)

        if len(args) <= 1:
            raise BadRequestError("指令格式不合法")

        if args[1].type == "text":
            if args[1].data["text"].startswith("对局"):
                # 以下两种格式：
                # 结算 对局<编号> <分数>
                # 结算 对局<编号> @<用户> <分数>
                game_id = args[1].data["text"][len("对局"):]

                if args[2].type == "text":
                    # 结算 对局<编号> <分数>
                    point = args[2].data["text"]
                elif args[2].type == "at":
                    # 结算 对局<编号> @<用户> <分数>
                    user_id = int(args[2].data["qq"])
                    point = args[3].data["text"]
                else:
                    raise BadRequestError("指令格式不合法")
            else:
                # 结算 <分数>
                point = args[1].data["text"]
        elif args[1].type == "at":
            # 结算 @<用户> <分数>
            user_id = int(args[1].data["qq"])
            point = args[2].data["text"]
        else:
            raise BadRequestError("指令格式不合法")

        if not game_id:
            raise BadRequestError("请指定对局编号")

        try:
            game_id = int(game_id)
        except ValueError:
            raise BadRequestError("对局编号不合法")

        try:
            point = int(point)
        except ValueError:
            raise BadRequestError("分数不合法")

        game = await game_record.record(game_id, user_id, point)

        with StringIO() as sb:
            if game.state == GameState.uncompleted or game.state == GameState.invalid_total_point:
                sb.write(f"成功记录到对局{game.game_id}，当前记录情况：\n\n")
            elif game.state == GameState.completed:
                sb.write(f"成功记录到对局{game.game_id}，对局已成功结算。当前记录情况：\n\n")

            sb.write(await build_game_record_text(game, bot, event))

            if game.state == GameState.invalid_total_point:
                sb.write("警告：分数之和不等于100000，对此消息回复“撤销结算”指令撤销你的分数后重新记录")

            send_result = await record_matcher.send(sb.getvalue())

        await save_context(game_id=game.game_id, message_id=send_result["message_id"], user_id=user_id)
    except BadRequestError as e:
        await record_matcher.send(e.message)


# 撤销结算
revert_record_matcher = on_command("撤销结算", priority=5)


@revert_record_matcher.handle()
async def revert_record(bot: Bot, event: GroupMessageEvent):
    try:
        user_id = event.user_id
        game_id = None

        context = await get_context(event)
        if context:
            user_id = context.extra.get("user_id", None)
            game_id = context.game_id

        args = split_message(event.message)

        if len(args) > 1:
            if args[1].type == "text":
                if args[1].data["text"].startswith("对局"):
                    # 以下两种格式：
                    # 撤销结算 对局<编号>
                    # 撤销结算 对局<编号> @<用户>
                    game_id = args[1].data["text"][len("对局"):]

                    if len(args) > 2 and args[2].type == "at":
                        # 撤销结算 对局<编号> @<用户>
                        user_id = args[2].data["qq"]
                    # else:
                    # 撤销结算 对局<编号>
            else:
                # 撤销结算 @<用户>
                user_id = int(args[1].data["qq"])
        # else:
        # 撤销结算

        try:
            game_id = int(game_id)
        except ValueError:
            raise BadRequestError("对局编号不合法")

        game = await game_record.revert_record(game_id, user_id)

        with StringIO() as sb:
            if game.state == GameState.uncompleted:
                sb.write(f"成功撤销记录到对局{game.game_id}，当前记录情况：\n\n")
            sb.write(await build_game_record_text(game, bot, event))

            send_result = await record_matcher.send(sb.getvalue())

        await save_context(game_id=game.game_id, message_id=send_result["message_id"], user_id=user_id)

    except BadRequestError as e:
        await revert_record_matcher.send(e.message)
