from random import randint
from nonebot.adapters import Message
from nonebot import on_command, on_keyword, on_message
from nonebot.rule import to_me
from nonebot.adapters import Bot, Event
from nonebot.params import CommandArg
import json


id_gets = on_command("id", priority=1)
@id_gets.handle()
async def getID(bot:Bot, event:Event):
    await bot.send(message=f"{str(event.get_log_string())}", event=event)
