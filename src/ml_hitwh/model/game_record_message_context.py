from sqlalchemy import Column, BigInteger, Integer, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from ml_hitwh.model import OrmBase


class GameRecordMessageContext(OrmBase):
    __tablename__ = "game_record_message_context"

    message_id = Column(BigInteger, primary_key=True)

    game_id = Column(Integer, ForeignKey("game.id"))
    game = relationship('Game', foreign_keys='GameRecordMessageContextOrm.game_id')

    create_time = Column(DateTime, server_default=func.now())
    extra = Column(JSON)
