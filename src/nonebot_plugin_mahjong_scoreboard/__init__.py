"""
nonebot-plugin-mahjong-scoreboard

@Author         : ssttkkl
@License        : MIT
@GitHub         : https://github.com/ssttkkl/nonebot-plugin-mahjong-scoreboard
"""
from nonebot import require

require("nonebot_plugin_localstore")
require("nonebot_plugin_session")
require("nonebot_plugin_sqlalchemy")
require("nonebot_plugin_apscheduler")
require("nonebot_plugin_gocqhttp_cross_machine_upload_file")

from .config import Config
from .controller import game_record, game_query, game_export, season_query, season_manage, season_user_point_query, \
    season_user_point_export, season_user_point_manage, game_statistics
from .utils.nonebot import default_cmd_start

__usage__ = f"""
对局：
- {game_record.new_game_matcher.__help_info__}
- {game_record.record_matcher.__help_info__}
- {game_record.revert_record_matcher.__help_info__}
- {game_record.set_record_point_matcher.__help_info__}
- {game_record.delete_game_matcher.__help_info__}
- {game_record.make_game_progress_matcher.__help_info__}
- {game_record.set_game_comment_matcher.__help_info__}

对局查询：
- {game_query.query_by_code_matcher.__help_info__}
- {game_query.query_user_recent_games_matcher.__help_info__}
- {game_query.query_group_recent_games_matcher.__help_info__}
- {game_query.query_user_uncompleted_games_matcher.__help_info__}
- {game_query.query_group_uncompleted_games_matcher.__help_info__}
- {game_export.export_season_games_matcher.__help_info__}
- {game_export.export_group_games_matcher.__help_info__}

赛季：
- {season_query.query_season_matcher.__help_info__}
- {season_query.query_all_seasons_matcher.__help_info__}
- {season_manage.new_season_matcher.__help_info__}
- {season_manage.start_season_matcher.__help_info__}
- {season_manage.finish_season_matcher.__help_info__}
- {season_manage.remove_season_matcher.__help_info__}

赛季查询：
- {season_user_point_query.query_season_ranking_matcher.__help_info__}
- {season_user_point_export.export_season_ranking_matcher.__help_info__}
- {season_user_point_query.query_season_point_matcher.__help_info__}
- {season_user_point_manage.set_season_user_point_matcher.__help_info__}
- {season_user_point_manage.reset_season_user_point_matcher.__help_info__}

数据统计：
- {game_statistics.query_user_statistics_matcher}
- {game_statistics.query_season_user_statistics_matcher}
- {game_statistics.query_season_user_trend_matcher}

以上命令格式中，以<>包裹的表示一个参数，以[]包裹的表示一个可选项。

详细说明：参见https://github.com/ssttkkl/nonebot-plugin-mahjong-scoreboard
""".strip()

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name='日麻寄分器',
    description='为群友提供日麻计分及榜单统计功能',
    usage=__usage__,
    type="application",
    homepage="https://github.com/ssttkkl/nonebot-plugin-mahjong-scoreboard",
    config=Config,
    supported_adapters={"~onebot.v11", "~qqguild"}
)

__all__ = ("__plugin_meta__", "__usage__")
