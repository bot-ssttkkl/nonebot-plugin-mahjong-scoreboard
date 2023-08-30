from typing import Optional, NamedTuple

from nonebot import Bot
from nonebot_plugin_session import Session, SessionIdType, SessionLevel
from pydantic import BaseModel


class PlatformId(NamedTuple):
    platform: str
    bot_type: str
    real_id: str

    def __str__(self):
        return "_".join(self)

    @classmethod
    def parse(cls, value: str) -> "PlatformId":
        return PlatformId(*value.split("_", maxsplit=2))


def get_platform_user_id(session: Session) -> PlatformId:
    return PlatformId.parse(session.get_id(SessionIdType.USER, include_bot_id=False))


def get_platform_group_id(session: Session) -> Optional[PlatformId]:
    # 如果消息来自私聊，则session.get_id(SessionIdType.GROUP)返回的结果与session.get_id(SessionIdType.USER)相同
    res = PlatformId.parse(session.get_id(SessionIdType.GROUP, include_bot_id=False))
    platform_user_id = get_platform_user_id(session)
    if res != platform_user_id:
        return res
    else:
        return None


def convert_platform_id_to_session(bot: Bot, platform_user_id: PlatformId,
                                   platform_group_id: Optional[PlatformId]) -> Session:
    id1 = platform_user_id.real_id
    id2 = None
    id3 = None
    if platform_group_id is not None:
        id_seg = platform_group_id.real_id.split("_", maxsplit=1)
        if len(id_seg) != 1:
            id2 = id_seg[1]
            id3 = id_seg[0]
        else:
            id2 = id_seg[0]

    level = SessionLevel.LEVEL0
    if id2 is None and id3 is None:
        level = SessionLevel.LEVEL1
    elif id3 is None:
        level = SessionLevel.LEVEL2
    else:
        level = SessionLevel.LEVEL3

    return Session(bot_id=bot.self_id, bot_type=platform_user_id.bot_type, platform=platform_user_id.platform,
                   level=level, id1=id1, id2=id2, id3=id3)


class User(BaseModel):
    id: int
    platform_user_id: PlatformId


class Group(BaseModel):
    id: int
    platform_group_id: PlatformId


__all__ = ("PlatformId", "User", "Group")
