from time import time

import pytest
from nonebot.adapters.onebot.v11.event import Sender

SELF_ID = 19191919
USER_ID = 114514
GROUP_ID = 114514
INCOME_MESSAGE_ID = 123456789

PREV_OUTCOME_MESSAGE_ID = 1234567
NEW_OUTCOME_MESSAGE_ID = 1234568


class MyTest:
    @pytest.fixture
    def env_variables(self, monkeypatch):
        monkeypatch.setenv("ml_mongo_conn_url", "114514")
        monkeypatch.setenv("ml_mongo_database_name", "1919810")

    @pytest.fixture
    def load_plugin(self, nonebug_init, env_variables):
        import nonebot
        nonebot.load_plugin("ml_hitwh")


def make_group_message_event(message, **kwargs):
    from nonebot.adapters.onebot.v11 import GroupMessageEvent

    kwargs.setdefault("time", int(time()))
    kwargs.setdefault("self_id", SELF_ID)
    kwargs.setdefault("post_type", "message")

    kwargs.setdefault("sub_type", "")
    kwargs.setdefault("user_id", USER_ID)
    kwargs.setdefault("message_type", "group")
    kwargs.setdefault("message_id", INCOME_MESSAGE_ID)
    kwargs.setdefault("original_message", message)
    kwargs.setdefault("raw_message", str(message))
    kwargs.setdefault("font", 14)
    kwargs.setdefault("sender", Sender(user_id=USER_ID))

    kwargs.setdefault("group_id", GROUP_ID)

    event = GroupMessageEvent(message=message, **kwargs)
    event.original_message = kwargs["original_message"]
    return event
