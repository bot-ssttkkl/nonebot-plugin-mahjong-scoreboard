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
    while True:
        global game_info
        id = randint(1000, 9999)
        if id not in game_info:
            break
    game_info[id] = []
    await bot.send(message="新建对局成功，对局编号为{}".format(id), event=event)


count = on_command("", priority=5)
# 计数用


@count.handle()
async def counts(bot: Bot, event: Event):
    global game_info
    nums = str(event.get_message()).split(" ")
    try:
        if int(nums[0]) in game_info:
            try:
                for i in range(len(nums)):
                    nums[i] = int(nums[i])
            except:
                await bot.send(message="输入的信息或许有误？", event=event)
        else:
            return
    except:
        return
    if len(nums) == 2:
        game_info[nums[0]].append([event.get_user_id(), nums[1]])
    elif len(nums) == 3:
        game_info[nums[0]].append([str(nums[2]), nums[1]])
    # await bot.send(message=str(game_info[nums[0]]), event=event)
    if len(game_info[nums[0]]) == 4:
        await bot.send(message=f"请检查输入：\n{str(game_info[nums[0]])}", event=event)
        del game_info[nums[0]]
        