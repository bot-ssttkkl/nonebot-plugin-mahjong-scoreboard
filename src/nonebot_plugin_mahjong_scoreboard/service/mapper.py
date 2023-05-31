from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..model import Game, Season, Group, User, SeasonUserPoint, GameProgress, GameRecord, SeasonUserPointChangeLog
from ..repository.data_model import GameOrm, GameProgressOrm, GameRecordOrm, GroupOrm, SeasonOrm, SeasonUserPointOrm, \
    UserOrm, SeasonUserPointChangeLogOrm


async def map_group(group: Optional[GroupOrm], session: AsyncSession) -> Optional[Group]:
    if group is None:
        return None
    return Group(id=group.id, platform_group_id=group.platform_group_id)


async def map_user(user: Optional[UserOrm], session: AsyncSession) -> Optional[User]:
    if user is None:
        return None
    return User(id=user.id, platform_user_id=user.platform_user_id)


async def map_season(season: Optional[SeasonOrm], session: AsyncSession) -> Optional[Season]:
    if season is None:
        return None
    group = await session.get(GroupOrm, season.group_id) if season.group_id is not None else None
    return Season(id=season.id, group=await map_group(group, session), state=season.state, code=season.code,
                  name=season.name, start_time=season.start_time, finish_time=season.finish_time, config=season.config)


async def map_game_record(game_record: Optional[GameRecordOrm], session: AsyncSession) -> Optional[GameRecord]:
    if game_record is None:
        return None
    user = await session.get(UserOrm, game_record.user_id) if game_record.user_id is not None else None
    return GameRecord(user=await map_user(user, session), wind=game_record.wind,
                      score=game_record.score, rank=game_record.rank,
                      raw_point=game_record.raw_point, point_scale=game_record.point_scale)


async def map_game_progress(game_progress: Optional[GameProgressOrm], session: AsyncSession) -> Optional[GameProgress]:
    if game_progress is None:
        return None
    return GameProgress(round=game_progress.round, honba=game_progress.honba)


async def map_game(game: Optional[GameOrm], session: AsyncSession) -> Optional[Game]:
    if game is None:
        return None
    group = await session.get(GroupOrm, game.group_id) if game.group_id is not None else None
    promoter = await session.get(UserOrm, game.promoter_user_id) if game.promoter_user_id is not None else None
    season = await session.get(SeasonOrm, game.season_id) if game.season_id is not None else None
    return Game(id=game.id, code=game.code,
                group=await map_group(group, session),
                promoter=await map_user(promoter, session),
                season=await map_season(season, session),
                player_and_wind=game.player_and_wind, state=game.state,
                records=[await map_game_record(r, session) for r in game.records],
                progress=await map_game_progress(game.progress, session),
                complete_time=game.complete_time, comment=game.comment)


async def map_season_user_point(sup: Optional[SeasonUserPointOrm], session: AsyncSession) -> Optional[SeasonUserPoint]:
    if sup is None:
        return None
    user = await session.get(UserOrm, sup.user_id) if sup.user_id is not None else None
    return SeasonUserPoint(user=await map_user(user, session), point=sup.point)


async def map_season_user_point_change_log(log: Optional[SeasonUserPointChangeLogOrm], session: AsyncSession) \
        -> Optional[SeasonUserPointChangeLog]:
    if log is None:
        return None
    user = await session.get(UserOrm, log.user_id) if log.user_id is not None else None
    related_game = await session.get(GameOrm, log.related_game_id) \
        if log.related_game_id is not None \
        else None
    return SeasonUserPointChangeLog(user=await map_user(user, session),
                                    change_type=log.change_type,
                                    change_point=log.change_point,
                                    related_game=await map_game(related_game, session),
                                    create_time=log.create_time)
