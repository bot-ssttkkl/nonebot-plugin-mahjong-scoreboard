from typing import List

from nonebot.adapters.onebot.v11 import Message, Bot, Event

from ...config import conf


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


async def send_forward_msg(bot: Bot, event: Event, messages: List[Message]):
    user_id = getattr(event, "user_id", None)
    group_id = getattr(event, "group_id", None)
    if group_id is not None:
        await send_group_forward_msg(bot, group_id, messages)
    else:
        await send_private_forward_msg(bot, user_id, messages)


async def send_msgs(bot: Bot, event: Event, messages: List[Message]):
    if len(messages) > 1 and conf.mahjong_scoreboard_send_forward_message:
        await send_forward_msg(bot, event, messages)
    else:
        for msg in messages:
            await bot.send(event, msg)
