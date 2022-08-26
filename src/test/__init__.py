from time import time
from typing import TYPE_CHECKING

import pytest
from nonebot.adapters.onebot.v11.event import Sender


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
    kwargs.setdefault("self_id", 19191919)
    kwargs.setdefault("post_type", "message")

    kwargs.setdefault("sub_type", "")
    kwargs.setdefault("user_id", 114514)
    kwargs.setdefault("message_type", "group")
    kwargs.setdefault("message_id", 123456789)
    kwargs.setdefault("original_message", message)
    kwargs.setdefault("raw_message", str(message))
    kwargs.setdefault("font", 14)
    kwargs.setdefault("sender", Sender(user_id=114514))

    kwargs.setdefault("group_id", 1919810)

    return GroupMessageEvent(message=message, **kwargs)
