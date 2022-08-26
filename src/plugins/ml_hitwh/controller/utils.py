from typing import List

from nonebot import Bot
from nonebot.adapters.onebot.v11 import Message, MessageSegment

__all__ = ("split_message", "get_user_name")


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
    """获取用户名，优先返回群昵称，其次返回用户昵称"""
    user_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
    return user_info["card"] or user_info["nickname"]
