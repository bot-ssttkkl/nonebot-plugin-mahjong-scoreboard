from sqlalchemy import text

from ..data_source import data_source


async def migrate_v2_to_v3():
    async with data_source.engine.begin() as conn:
        await conn.execute(text("ALTER TABLE users ADD platform_user_id varchar NOT NULL DEFAULT '';"))
        await conn.execute(text("UPDATE users SET platform_user_id = 'qq_OneBot V11_' || binding_qq;"))

        if data_source.dialect == 'sqlite':
            await conn.execute(text("""
                create table users_dg_tmp
                (
                    id               INTEGER not null
                        primary key,
                    platform_user_id varchar default '' not null
                );
                """))

            await conn.execute(text("""
                insert into users_dg_tmp(id, platform_user_id)
                select id, platform_user_id
                from users;
            """))

            await conn.execute(text("drop table users;"))

            await conn.execute(text("alter table users_dg_tmp rename to users;"))
        else:
            await conn.execute(text("ALTER TABLE users DROP COLUMN binding_qq;"))

        await conn.execute(text("ALTER TABLE groups ADD platform_group_id varchar NOT NULL DEFAULT '';"))
        await conn.execute(text("UPDATE groups SET platform_group_id = 'qq_OneBot V11_' || binding_qq;"))

        if data_source.dialect == 'sqlite':
            await conn.execute(text("""
            create table groups_dg_tmp
            (
                id                        INTEGER not null
                    primary key,
                running_season_id         INTEGER
                    references seasons,
                prev_game_code_base       INTEGER not null,
                prev_game_code_identifier INTEGER not null,
                platform_group_id          varchar default '' not null
            );
            """))

            await conn.execute(text("""
                insert into groups_dg_tmp(id, running_season_id, prev_game_code_base, prev_game_code_identifier, platform_group_id)
                select id, running_season_id, prev_game_code_base, prev_game_code_identifier, platform_group_id
                from groups;
            """))

            await conn.execute(text("drop table groups;"))

            await conn.execute(text("alter table groups_dg_tmp rename to groups;"))
        else:
            await conn.execute(text("ALTER TABLE groups DROP COLUMN binding_qq;"))
