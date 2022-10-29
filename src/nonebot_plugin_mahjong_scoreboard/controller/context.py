from cachetools import TTLCache
from nonebot.adapters.onebot.v11 import MessageEvent

context = TTLCache(maxsize=4096, ttl=7200)


def get_context(event: MessageEvent):
    message_id = None
    for seg in event.original_message:
        if seg.type == "reply":
            message_id = int(seg.data["id"])
            break

    if message_id:
        return context.get(message_id, None)


def save_context(message_id: int, **kwargs):
    context[message_id] = kwargs
