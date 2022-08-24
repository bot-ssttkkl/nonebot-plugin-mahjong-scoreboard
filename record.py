from audioop import reverse
from random import randint
from nonebot.adapters import Message
from nonebot import on_command, on_keyword, on_message
from nonebot.rule import to_me
from nonebot.adapters import Bot, Event
from nonebot.params import CommandArg
import json


game_info = {}
# 当前对局列表


create = on_command("新建对局", aliases=set(tuple(["xj", "new"])), priority=5)
# 用户新建对局


@create.handle()
async def new_game(bot: Bot, event: Event):
    global game_info
    if event.get_event_name() != "message.group.normal":
        await bot.send(message="请在群聊中使用此功能！", event=event)
        return
    group_id = str(event.get_session_id()).split("_")[1]
    game_info[group_id] = []
    await bot.send(message="新建对局成功", event=event)


count = on_command("结算", priority=5)
# 计数用


@count.handle()
async def counts(bot: Bot, event: Event):
    if event.get_event_name() != "message.group.normal":
        await bot.send(message="请在群聊中使用此功能！", event=event)
        return
    global game_info
    group_id = str(event.get_session_id()).split("_")[1]
    if group_id not in game_info:
        await bot.send(message="当前并没有正在进行的对局！", event=event)
        return
    whatever, user, credit = str(event.get_message()).split(" ")
    try:
        credit = int(credit)
    except:
        await bot.send(message="输入是否有错误？", event=event)
        return
    game_info[group_id].append([user, credit])
    await bot.send(message=f"已记录数据：{user} {credit}", event=event)
    if len(game_info[group_id]) == 4:
        counts = 0
        for info in game_info[group_id]:
            counts += info[1]
        if counts != 100000:
            await bot.send(message="输入是否有错误？总数错误", event=event)
        game_info[group_id].sort(key = lambda item: item[1], reverse = True)
        info = "信息已输入，请确认信息：\n"
        info += f"{game_info[group_id][0][0]}\t\t{game_info[group_id][0][1]}\t\t1位\n"
        info += f"{game_info[group_id][1][0]}\t\t{game_info[group_id][1][1]}\t\t2位\n"
        info += f"{game_info[group_id][2][0]}\t\t{game_info[group_id][2][1]}\t\t3位\n"
        info += f"{game_info[group_id][3][0]}\t\t{game_info[group_id][3][1]}\t\t4位"
        await bot.send(event = event, message=info)
        del game_info[group_id]