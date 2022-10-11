from typing import List, Optional

from nonebot import Bot
from nonebot.adapters.onebot.v11 import Message, MessageSegment, MessageEvent


def get_reply_message_id(event: MessageEvent) -> Optional[int]:
    message_id = None
    for seg in event.original_message:
        if seg.type == "reply":
            message_id = int(seg.data["id"])
            break
    return message_id


def split_message(message: Message) -> List[MessageSegment]:
    result = []
    for seg in message:
        if seg.type == "text":
            for text in seg.data["text"].split(" "):
                if text:
                    result.append(MessageSegment.text(text))
        else:
            result.append(seg)

    return result


async def get_user_name(user_id: int, group_id: int, bot: Bot):
    user_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
    return user_info["card"] or user_info["nickname"]
