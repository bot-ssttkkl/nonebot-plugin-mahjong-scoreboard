from datetime import datetime
from unittest.mock import AsyncMock

import pytest
import tzlocal
from nonebug import App

from test import MyTest, make_group_message_event, NEW_OUTCOME_MESSAGE_ID, USER_ID, GROUP_ID
from test.controller.game_record.fake_context_manager import FakeContextManagerMixin
from test.controller.game_record.test_record import GAME_ID


class TestNewGame(FakeContextManagerMixin,
                  MyTest):

    @pytest.fixture
    def mock_new_game_service(self, load_plugin, monkeypatch):
        from ml_hitwh.model.game import GameModel, Wind

        async def new_game(create_user_id: int, group_id: int, players: int, wind: Wind) -> GameModel:
            game = GameModel(game_id=GAME_ID,
                             group_id=group_id,
                             players=players,
                             wind=wind,
                             create_user_id=create_user_id,
                             create_time=datetime.now(tzlocal.get_localzone()))

            return game

        new_game = AsyncMock(side_effect=new_game)
        monkeypatch.setattr("ml_hitwh.service.game_record.new_game", new_game)
        return new_game

    @pytest.fixture
    def factory_test_new_game(self, app: App,
                              mock_new_game_service, mock_save_context,
                              load_plugin):
        from nonebot.adapters.onebot.v11 import Message
        from ml_hitwh.controller.game_record import new_game_matcher

        async def test_new_game(message: Message,
                                expect_msg: str,
                                should_success: bool = False):
            async with app.test_matcher(new_game_matcher) as ctx:
                bot = ctx.create_bot()
                event = make_group_message_event(message=message)

                ctx.receive_event(bot, event)
                ctx.should_call_send(event, expect_msg, {"message_id": NEW_OUTCOME_MESSAGE_ID})

            if should_success:
                mock_new_game_service.assert_awaited_once()
                mock_save_context.assert_awaited_once_with(game_id=GAME_ID, message_id=NEW_OUTCOME_MESSAGE_ID)
            else:
                mock_new_game_service.assert_not_awaited()
                mock_save_context.assert_not_awaited()

        return test_new_game

    @pytest.mark.asyncio
    async def test_new_game_1(self, factory_test_new_game, mock_new_game_service):
        from nonebot.adapters.onebot.v11 import Message, MessageSegment
        from ml_hitwh.model.game import Wind

        message = Message(MessageSegment.text("/新建对局"))
        expect_msg = f"成功新建对局{GAME_ID}，对此消息回复“/结算 <分数>”指令记录你的分数"
        await factory_test_new_game(message, expect_msg, True)

        mock_new_game_service.assert_awaited_once_with(USER_ID, GROUP_ID, 4, Wind.SOUTH)

    @pytest.mark.asyncio
    async def test_new_game_2(self, factory_test_new_game, mock_new_game_service):
        from nonebot.adapters.onebot.v11 import Message, MessageSegment
        from ml_hitwh.model.game import Wind

        message = Message(MessageSegment.text("/新建对局 四人东"))
        expect_msg = f"成功新建对局{GAME_ID}，对此消息回复“/结算 <分数>”指令记录你的分数"
        await factory_test_new_game(message, expect_msg, True)

        mock_new_game_service.assert_awaited_once_with(USER_ID, GROUP_ID, 4, Wind.EAST)

    @pytest.mark.asyncio
    async def test_new_game_2(self, factory_test_new_game, mock_new_game_service):
        from nonebot.adapters.onebot.v11 import Message, MessageSegment
        from ml_hitwh.model.game import Wind

        message = Message(MessageSegment.text("/新建对局 四人南"))
        expect_msg = f"成功新建对局{GAME_ID}，对此消息回复“结算 <分数>”指令记录你的分数"
        await factory_test_new_game(message, expect_msg, True)

        mock_new_game_service.assert_awaited_once_with(USER_ID, GROUP_ID, 4, Wind.SOUTH)

    @pytest.mark.asyncio
    async def test_new_game_3(self, factory_test_new_game, mock_new_game_service):
        from nonebot.adapters.onebot.v11 import Message, MessageSegment
        from ml_hitwh.model.game import Wind

        message = Message(MessageSegment.text("/新建对局 三人东"))
        expect_msg = f"成功新建对局{GAME_ID}，对此消息回复“结算 <分数>”指令记录你的分数"
        await factory_test_new_game(message, expect_msg, True)

        mock_new_game_service.assert_awaited_once_with(USER_ID, GROUP_ID, 3, Wind.EAST)

    @pytest.mark.asyncio
    async def test_new_game_4(self, factory_test_new_game, mock_new_game_service):
        from nonebot.adapters.onebot.v11 import Message, MessageSegment
        from ml_hitwh.model.game import Wind

        message = Message(MessageSegment.text("/新建对局 三人南"))
        expect_msg = f"成功新建对局{GAME_ID}，对此消息回复“结算 <分数>”指令记录你的分数"
        await factory_test_new_game(message, expect_msg, True)

        mock_new_game_service.assert_awaited_once_with(USER_ID, GROUP_ID, 3, Wind.SOUTH)

    @pytest.mark.asyncio
    async def test_new_game_5(self, factory_test_new_game, mock_new_game_service):
        from nonebot.adapters.onebot.v11 import Message, MessageSegment

        message = Message(MessageSegment.text("/新建对局 三人什么几把南"))
        expect_msg = "对局类型不合法"
        await factory_test_new_game(message, expect_msg, False)
