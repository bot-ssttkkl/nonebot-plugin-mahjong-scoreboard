from sqlalchemy import select

from ml_hitwh.model import SQLSession
from ml_hitwh.model.game_record_message_context import GameRecordMessageContext


async def get_context(message_id: int) -> GameRecordMessageContext:
    async with SQLSession() as session:
        stmt = select(GameRecordMessageContext).where(GameRecordMessageContext.message_id == message_id)
        result = await session.execute(stmt)
        return result.first()


async def save_context(game_id: int, message_id: int, **kwargs):
    async with SQLSession() as session:
        context = GameRecordMessageContext(message_id=message_id, game_id=game_id, extra=kwargs)
        await session.add(context)
        await session.commit()
