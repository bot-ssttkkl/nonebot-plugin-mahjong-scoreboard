from io import StringIO

from . import season_state_mapping, map_datetime
from ...model import Season, RankPointPolicy

rank_point_policy_mapping = {
    RankPointPolicy.absolute_rank_point: "绝对顺位点",
    RankPointPolicy.first_rank_prize: "头名赏",
    RankPointPolicy.horse_point: "马点",
    RankPointPolicy.overwater: "水上顺位点"
}

rank_point_policy_description = {
    RankPointPolicy.absolute_rank_point: "（PT由顺位唯一确定，与其他策略互斥）",
    RankPointPolicy.first_rank_prize: "（计算成绩时，将所有人的返点减去点数作为给1位的额外加点）",
    RankPointPolicy.horse_point: "（指计算成绩时，给不同名次的人进行额外PT奖惩）",
    RankPointPolicy.overwater: "（日本职业麻将联盟竞技规则，A规，与其他策略互斥）"
}


def map_rank_point_policy(policy: int, with_description: bool = False) -> str:
    res = []
    for x in list(RankPointPolicy):
        if policy & x:
            res.append(rank_point_policy_mapping[x])
            if with_description:
                res[-1] += rank_point_policy_description[x]
    return '，'.join(res)


def map_season(season: Season, detailed: bool = False) -> str:
    with StringIO() as io:
        # {season.name}
        io.write(season.name)
        io.write('\n')

        # 代号：{season.code}
        io.write('代号：')
        io.write(season.code)
        io.write('\n')

        if season.state:
            io.write('状态：')
            io.write(season_state_mapping[season.state])
            io.write('\n')

        if season.start_time:
            io.write('开始时间：')
            io.write(map_datetime(season.start_time))
            io.write('\n')

        if season.finish_time:
            io.write('结束时间：')
            io.write(map_datetime(season.finish_time))
            io.write('\n')

        io.write(f"顺位PT策略：{map_rank_point_policy(season.config.rank_point_policy)}\n")

        if detailed:
            # 半庄战：起点：25000  返点：30000  顺位点：50 30 -10 -30
            io.write('半庄战：')
            if season.config.south_game_enabled:
                io.write(f'起点：{season.config.south_game_initial_point}')
                io.write(f'  返点：{season.config.south_game_origin_point}')
                if season.config.rank_point_policy & RankPointPolicy.absolute_rank_point \
                        or season.config.rank_point_policy & RankPointPolicy.horse_point:
                    io.write('  顺位点：[')
                    io.write(' '.join(map(str, season.config.south_game_horse_point)))
                    io.write(']')
                if season.config.rank_point_policy & RankPointPolicy.overwater:
                    io.write('  水上顺位点：')
                    for i, arr_1d in enumerate(season.config.south_game_overwater_point):
                        io.write(f'{i}人：[')
                        io.write(' '.join(map(str, arr_1d)))
                        io.write(']')
                        if i != len(season.config.south_game_overwater_point):
                            io.write('，')
            else:
                io.write('关闭')
            io.write('\n')

            # 东风战：关闭
            io.write('东风战：')
            if season.config.east_game_enabled:
                io.write(f'起点：{season.config.east_game_initial_point}')
                io.write(f'  返点：{season.config.east_game_origin_point}')
                if season.config.rank_point_policy & RankPointPolicy.absolute_rank_point \
                        or season.config.rank_point_policy & RankPointPolicy.horse_point:
                    io.write('  顺位点：[')
                    io.write(' '.join(map(str, season.config.east_game_horse_point)))
                    io.write(']')
                if season.config.rank_point_policy & RankPointPolicy.overwater:
                    io.write('  水上顺位点：')
                    for i, arr_1d in enumerate(season.config.east_game_overwater_point):
                        io.write(f'{i}人：[')
                        io.write(' '.join(map(str, arr_1d)))
                        io.write(']')
                        if i != len(season.config.east_game_overwater_point):
                            io.write('，')
            else:
                io.write('关闭')
            io.write('\n')

            # PT精度：1
            io.write('PT精度：')
            io.write(str(10 ** season.config.point_precision))
            io.write('\n')

        return io.getvalue().strip()
