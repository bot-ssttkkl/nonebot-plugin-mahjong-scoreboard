"""
nonebot-plugin-mahjong-scoreboard

@Author         : ssttkkl
@License        : MIT
@GitHub         : https://github.com/ssttkkl/nonebot-plugin-mahjong-scoreboard
"""

help_text = """
对局：
- 新建对局 [四人南|四人东]
- 结算对局 <成绩> [对局<编号>] [@<用户>] [<自风>]
- 撤销结算对局 [对局<编号>] [@<用户>]
- 设置对局PT <PT> [对局<编号>] [@<用户>]
- 删除对局 [对局<编号>]
- 设置对局进度 <进度> [对局<编号>]

对局查询：
- 查询对局 [<编号>]
- 个人最近对局 [@<用户>]
- 群最近对局
- 个人未完成对局 [@<用户>]
- 群未完成对局
- 导出赛季对局 [<代号>]
- 导出所有对局

赛季：
- 查询赛季 [<代号>]
- 查询所有赛季
- 新建赛季
- 开启赛季 [<代号>]
- 结束赛季
- 删除赛季 [<代号>]

赛季PT：
- 设置赛季PT <PT> [@<用户>]
- 查询PT [@<用户>]
- 查询榜单
- 导出榜单

以上命令格式中，以<>包裹的表示一个参数，以[]包裹的表示一个可选项。

详细说明：参见https://github.com/ssttkkl/nonebot-plugin-mahjong-scoreboard
""".strip()

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name='日麻寄分器',
    description='为群友提供日麻计分及榜单统计功能',
    usage=help_text,
    extra={'version': '0.1.0'}
)

from . import controller
