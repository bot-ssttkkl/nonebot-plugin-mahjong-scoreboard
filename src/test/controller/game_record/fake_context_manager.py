from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from test import MyTest

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11 import GroupMessageEvent

context = {}


class FakeContextManagerMixin(MyTest):
    @staticmethod
    async def actual_save_context(game_id: int, message_id: int, **kwargs):
        from ml_hitwh.model.game_record_message_context import GameRecordMessageContextModel
        context[message_id] = GameRecordMessageContextModel(game_id=game_id, message_id=message_id, extra=kwargs)

    @pytest.fixture(autouse=True)
    def mock_save_context(self, load_plugin, monkeypatch):
        save_context = AsyncMock(side_effect=self.actual_save_context)
        monkeypatch.setattr("ml_hitwh.controller.game_record.save_context", save_context)
        return save_context

    @staticmethod
    async def actual_get_context(event: "GroupMessageEvent"):
        message_id = None
        for seg in event.original_message:
            if seg.type == "reply":
                message_id = int(seg.data["id"])
                break

        if message_id:
            return context[message_id]

    @pytest.fixture(autouse=True)
    def mock_get_context(self, load_plugin, monkeypatch):
        get_context = AsyncMock(side_effect=self.actual_get_context)
        monkeypatch.setattr("ml_hitwh.controller.game_record.get_context", get_context)
        return get_context
