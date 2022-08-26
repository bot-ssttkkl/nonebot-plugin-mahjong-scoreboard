from datetime import datetime
from unittest.mock import AsyncMock

import pytest
import tzlocal
from nonebug import App

from test import MyTest, make_group_message_event
from test.controller.game_record.fake_context_manager import FakeContextManagerMixin

GAME_ID = 22082601
MESSAGE_ID = 987654321


class TestNewGame(FakeContextManagerMixin,
                  MyTest):

    @pytest.fixture
    def mock_new_game_service(self, load_plugin, monkeypatch):
        from ml_hitwh.model.game import GameModel

        async def new_game(create_user_id: int, group_id: int) -> GameModel:
            now = datetime.now(tzlocal.get_localzone())
            game_id = GAME_ID
            game = GameModel(game_id=game_id,
                             group_id=group_id,
                             create_user_id=create_user_id,
                             create_time=now)

            return game

        new_game = AsyncMock(side_effect=new_game)

        monkeypatch.setattr("ml_hitwh.service.game_record.new_game", new_game)

        return new_game

    @pytest.mark.asyncio
    async def test_new_game(self, app: App,
                            mock_new_game_service, mock_save_context,
                            load_plugin):
        from nonebot.adapters.onebot.v11 import Message, MessageSegment
        from ml_hitwh.controller.game_record import new_game_matcher

        async with app.test_matcher(new_game_matcher) as ctx:
            bot = ctx.create_bot()
            msg = Message([MessageSegment.text("/新建对局")])
            event = make_group_message_event(message=msg)

            ctx.receive_event(bot, event)

            expect_msg = f"成功新建对局{GAME_ID}，对此消息回复“结算 <分数>”指令记录你的分数"
            ctx.should_call_send(event, expect_msg, {"message_id": MESSAGE_ID})

        mock_new_game_service.assert_awaited_once()
        mock_save_context.assert_awaited_once_with(game_id=GAME_ID, message_id=MESSAGE_ID)