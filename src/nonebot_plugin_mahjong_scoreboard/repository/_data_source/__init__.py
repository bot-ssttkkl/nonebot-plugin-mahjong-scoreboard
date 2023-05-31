from asyncio import Lock

from nonebot import logger
from nonebot.internal.matcher import current_matcher

from .data_source import data_source
from .metainfo import set_metainfo, get_metainfo, APP_DB_VERSION
from .migrations import migrations


@data_source.on_remove_session
async def acquire_mutex():
    matcher = current_matcher.get()
    if "db_mutex" in matcher.state:
        db_mutex: Lock = matcher.state["db_mutex"]
        await db_mutex.acquire()


@data_source.on_session_removed
def release_mutex():
    matcher = current_matcher.get()
    if "db_mutex" in matcher.state:
        db_mutex: Lock = matcher.state["db_mutex"]
        db_mutex.release()


@data_source.on_ready
async def do_migrate():
    cur_db_version = await get_metainfo('db_version')
    while cur_db_version < APP_DB_VERSION:
        mig = migrations[cur_db_version, cur_db_version + 1]
        await mig()
        await set_metainfo('db_version', cur_db_version + 1)
        logger.success(f"migrate database from version {cur_db_version} to version {cur_db_version + 1}")

        cur_db_version += 1


__all__ = ("data_source",)
