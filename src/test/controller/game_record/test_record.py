from datetime import datetime
from typing import Union
from unittest.mock import AsyncMock

import pytest
import tzlocal
from nonebug import App

from test import MyTest, make_group_message_event, SELF_ID, PREV_OUTCOME_MESSAGE_ID, NEW_OUTCOME_MESSAGE_ID, GROUP_ID, \
    USER_ID
from test.controller.game_record.fake_context_manager import FakeContextManagerMixin

GAME_ID = 22082601


class TestRecord(FakeContextManagerMixin, MyTest):
    @pytest.fixture
    def mock_record_factory(self, load_plugin, monkeypatch):
        from ml_hitwh.model.game import GameModel

        def factory(result: Union[GameModel, Exception]):
            async def record(game_id: int, user_id: int, point: int) -> GameModel:
                if isinstance(result, Exception):
                    raise result
                else:
                    return result

            record = AsyncMock(side_effect=record)
            monkeypatch.setattr("ml_hitwh.service.game_record.record", record)
            return record

        return factory

    @pytest.fixture
    def factory_test_record(self, app: App,
                            mock_get_context, mock_save_context,
                            mock_record_factory,
                            load_plugin):
        from nonebot.adapters.onebot.v11 import Message
        from ml_hitwh.model.game import GameModel

        async def test_record(message: Message,
                              reply: bool,
                              result_game: Union[GameModel, Exception, None],
                              expect_msg: str,
                              should_success: bool = False):
            from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot
            from ml_hitwh.controller.game_record import record_matcher

            if reply:
                original_message = Message([MessageSegment.reply(PREV_OUTCOME_MESSAGE_ID),
                                            MessageSegment.at(SELF_ID),
                                            *message])
            else:
                original_message = message
            event = make_group_message_event(message=message, original_message=original_message)

            mock_record = mock_record_factory(result_game)

            await self.actual_save_context(GAME_ID, PREV_OUTCOME_MESSAGE_ID)

            async with app.test_matcher(record_matcher) as ctx:
                bot = ctx.create_bot(base=Bot, self_id=SELF_ID)

                ctx.receive_event(bot, event)
                if should_success:
                    ctx.should_call_api("get_group_member_info", {"user_id": USER_ID, "group_id": GROUP_ID},
                                        {"card": "", "nickname": "TESTUSER"})
                ctx.should_call_send(event, expect_msg, {"message_id": NEW_OUTCOME_MESSAGE_ID})

            if should_success:
                mock_record.assert_awaited_once()
                mock_save_context.assert_awaited_once_with(game_id=GAME_ID, message_id=NEW_OUTCOME_MESSAGE_ID,
                                                           user_id=USER_ID)

        return test_record

    # ========== should success ==========

    @pytest.mark.asyncio
    async def test_record_1(self, factory_test_record):
        # [引用消息]/结算 20000
        from nonebot.adapters.onebot.v11 import Message, MessageSegment
        from ml_hitwh.model.game import GameModel, GameRecord

        msg = Message([MessageSegment.text("/结算 20000")])
        result_game = GameModel(game_id=GAME_ID,
                                group_id=GROUP_ID,
                                create_user_id=USER_ID,
                                create_time=datetime.now(tzlocal.get_localzone()),
                                record=[GameRecord(user_id=USER_ID, point=20000)])
        expect_msg = "成功记录到对局22082601，当前记录情况：\n" \
                     "\n" \
                     "#1  TESTUSER\t 20000\n"

        await factory_test_record(msg, True, result_game, expect_msg, )

    @pytest.mark.asyncio
    async def test_record_2(self, factory_test_record):
        # /结算 对局22082601 20000
        from nonebot.adapters.onebot.v11 import Message, MessageSegment
        from ml_hitwh.model.game import GameModel, GameRecord

        msg = Message([MessageSegment.text(f"/结算 对局{GAME_ID} 20000")])
        result_game = GameModel(game_id=GAME_ID,
                                group_id=GROUP_ID,
                                create_user_id=USER_ID,
                                create_time=datetime.now(tzlocal.get_localzone()),
                                record=[GameRecord(user_id=USER_ID, point=20000)])
        expect_msg = "成功记录到对局22082601，当前记录情况：\n" \
                     "\n" \
                     "#1  TESTUSER\t 20000\n"

        await factory_test_record(msg, False, result_game, expect_msg, )

    @pytest.mark.asyncio
    async def test_record_3(self, factory_test_record):
        # [引用]/结算 @用户 20000
        from nonebot.adapters.onebot.v11 import Message, MessageSegment
        from ml_hitwh.model.game import GameModel, GameRecord

        msg = Message([MessageSegment.text(f"/结算 "), MessageSegment.at(USER_ID), MessageSegment.text("20000")])
        result_game = GameModel(game_id=GAME_ID,
                                group_id=GROUP_ID,
                                create_user_id=USER_ID,
                                create_time=datetime.now(tzlocal.get_localzone()),
                                record=[GameRecord(user_id=USER_ID, point=20000)])
        expect_msg = "成功记录到对局22082601，当前记录情况：\n" \
                     "\n" \
                     "#1  TESTUSER\t 20000\n"

        await factory_test_record(msg, True, result_game, expect_msg, )

    @pytest.mark.asyncio
    async def test_record_4(self, factory_test_record):
        # /结算 对局22082601 @用户 20000
        from nonebot.adapters.onebot.v11 import Message, MessageSegment
        from ml_hitwh.model.game import GameModel, GameRecord

        msg = Message([MessageSegment.text(f"/结算 对局22082601 "),
                       MessageSegment.at(USER_ID), MessageSegment.text("20000")])
        result_game = GameModel(game_id=GAME_ID,
                                group_id=GROUP_ID,
                                create_user_id=USER_ID,
                                create_time=datetime.now(tzlocal.get_localzone()),
                                record=[GameRecord(user_id=USER_ID, point=20000)])
        expect_msg = "成功记录到对局22082601，当前记录情况：\n" \
                     "\n" \
                     "#1  TESTUSER\t 20000\n"

        await factory_test_record(msg, False, result_game, expect_msg, )

    # ========== should fail ==========

    @pytest.mark.asyncio
    async def test_record_5(self, factory_test_record):
        # /结算 20000
        from nonebot.adapters.onebot.v11 import Message, MessageSegment

        msg = Message([MessageSegment.text("/结算 20000")])
        expect_msg = "请指定对局编号"

        await factory_test_record(msg, False, None, expect_msg, False)

    @pytest.mark.asyncio
    async def test_record_6(self, factory_test_record):
        # /结算 @用户 20000
        from nonebot.adapters.onebot.v11 import Message, MessageSegment

        msg = Message([MessageSegment.text(f"/结算"),
                       MessageSegment.at(USER_ID), MessageSegment.text("20000")])
        expect_msg = "请指定对局编号"

        await factory_test_record(msg, False, None, expect_msg, False)

    @pytest.mark.asyncio
    async def test_record_7(self, factory_test_record):
        # /结算
        from nonebot.adapters.onebot.v11 import Message, MessageSegment

        msg = Message([MessageSegment.text("/结算")])
        expect_msg = "指令格式不合法"

        await factory_test_record(msg, False, None, expect_msg, False)

    @pytest.mark.asyncio
    async def test_record_8(self, factory_test_record):
        # [引用消息]/结算 20000
        from nonebot.adapters.onebot.v11 import Message, MessageSegment
        from ml_hitwh.errors import BadRequestError

        msg = Message([MessageSegment.text("/结算 20000")])
        expect_msg = "Service层透传异常"
        raises = BadRequestError(expect_msg)

        await factory_test_record(msg, True, raises, expect_msg, False)
