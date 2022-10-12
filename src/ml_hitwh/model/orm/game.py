from sqlalchemy import Column, Integer, Enum, DateTime, func, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from . import OrmBase
from ..enums import PlayerAndWind, GameState


class GameOrm(OrmBase):
    __tablename__ = 'games'

    # 应用使用的ID（全局唯一）
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 外部使用的代号（群组内唯一）
    code = Column(Integer, nullable=False)

    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship('GroupOrm', foreign_keys='GameOrm.group_id')

    promoter_user_id = Column(Integer, ForeignKey('users.id'))
    promoter = relationship('UserOrm', foreign_keys='GameOrm.promoter_user_id')

    season_id = Column(Integer, ForeignKey('seasons.id'))
    season = relationship('SeasonOrm', foreign_keys='GameOrm.season_id')

    player_and_wind = Column(Enum(PlayerAndWind), nullable=False,
                             default=PlayerAndWind.four_men_south)
    state = Column(Enum(GameState), nullable=False, default=GameState.uncompleted)

    records = relationship("GameRecordOrm", foreign_keys='GameRecordOrm.game_id', back_populates="game")

    accessible = Column(Boolean, nullable=False, default=True)
    create_time = Column(DateTime, nullable=False, server_default=func.now())
    update_time = Column(DateTime)
    delete_time = Column(DateTime)


class GameRecordOrm(OrmBase):
    __tablename__ = 'game_records'

    game_id = Column(Integer, ForeignKey('games.id'), primary_key=True, nullable=False)
    game = relationship('GameOrm', foreign_keys='GameRecordOrm.game_id', back_populates='records')

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    user = relationship('UserOrm', foreign_keys='GameRecordOrm.user_id')

    score = Column(Integer, nullable=False)  # 分数
    point = Column(Integer)  # pt


__all__ = ("GameOrm", "GameRecordOrm")
