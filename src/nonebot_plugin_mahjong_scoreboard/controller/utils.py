from typing import List, Optional, Union

from nonebot.adapters.onebot.v11 import Message, MessageSegment, MessageEvent, ActionFailed, Bot
from nonebot.internal.matcher import current_bot, current_matcher

from nonebot_plugin_mahjong_scoreboard.errors import BadRequestError
from nonebot_plugin_mahjong_scoreboard.model.enums import Wind
from nonebot_plugin_mahjong_scoreboard.utils.integer import decode_integer


def get_reply_message_id(event: MessageEvent) -> Optional[int]:
    message_id = None
    for seg in event.original_message:
        if seg.type == "reply":
            message_id = int(seg.data["id"])
            break
    return message_id


def split_message(message: Message, ignore_empty: bool = True) -> List[MessageSegment]:
    result = []
    for seg in message:
        if seg.type == "text":
            for text in seg.data["text"].split(" "):
                if not ignore_empty or text:
                    result.append(MessageSegment.text(text))
        else:
            result.append(seg)

    return result


async def get_group_info(group_binding_qq: int):
    bot = current_bot.get()
    try:
        group_info = await bot.get_group_info(group_id=group_binding_qq)
        # 如果机器人尚未加入群, group_create_time, group_level, max_member_count 和 member_count 将会为0
        if group_info["member_count"] == 0:
            raise BadRequestError("机器人尚未加入群")
        return group_info
    except ActionFailed as e:
        raise BadRequestError(e.info["wording"])


def parse_int_or_error(raw: Union[int, str, None], desc: str, allow_chinese: bool = False) -> int:
    if not raw:
        raise BadRequestError(f"请指定{desc}")

    try:
        if allow_chinese:
            return decode_integer(raw)
        else:
            return int(raw)
    except ValueError:
        raise BadRequestError(f"输入的{desc}不合法")


async def parse_int_or_reject(raw: Union[int, str, None], desc: str, allow_chinese: bool = False) -> int:
    matcher = current_matcher.get()
    if not raw:
        await matcher.reject(f"请指定{desc}")

    try:
        if allow_chinese:
            return decode_integer(raw)
        else:
            return int(raw)
    except ValueError:
        await matcher.reject(f"输入的{desc}不合法。请重新输入")


def try_parse_wind(text: str) -> Optional[Wind]:
    if text == "东":
        return Wind.east
    if text == "南":
        return Wind.south
    if text == "西":
        return Wind.west
    if text == "北":
        return Wind.north
    return None


async def send_group_forward_msg(bot: Bot, group_id: int, messages: List[Message]):
    self_info = await bot.get_login_info()

    msg_li = []

    for msg in messages:
        msg_li.append({
            "type": "node",
            "data": {
                "uin": bot.self_id,
                "name": self_info["nickname"],
                "content": msg
            }
        })

    await bot.send_group_forward_msg(group_id=group_id, messages=msg_li)


async def send_private_forward_msg(bot: Bot, user_id: int, messages: List[Message]):
    self_info = await bot.get_login_info()

    msg_li = []

    for msg in messages:
        msg_li.append({
            "type": "node",
            "data": {
                "uin": bot.self_id,
                "name": self_info["nickname"],
                "content": msg
            }
        })

    await bot.send_private_forward_msg(user_id=user_id, messages=msg_li)
