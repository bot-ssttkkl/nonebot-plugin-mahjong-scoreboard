from nonebot import logger

from .v1_to_v2 import migrate_v1_to_v2
from ..metainfo import get_metainfo, APP_DB_VERSION, set_metainfo
from ..src import data_source

migrations = {
    (1, 2): migrate_v1_to_v2
}


@data_source.on_ready
async def do_migrate():
    cur_db_version = await get_metainfo('db_version')
    while cur_db_version < APP_DB_VERSION:
        mig = migrations[cur_db_version, cur_db_version + 1]
        await mig()
        await set_metainfo('db_version', cur_db_version + 1)
        logger.success(f"migrate database from version {cur_db_version} to version {cur_db_version + 1}")

        cur_db_version += 1
