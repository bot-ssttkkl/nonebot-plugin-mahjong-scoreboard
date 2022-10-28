from nonebot_plugin_mahjong_scoreboard.model.enums import PlayerAndWind, GameState, SeasonState, Wind

player_and_wind_mapping = {
    PlayerAndWind.four_men_east: '四人东',
    PlayerAndWind.four_men_south: '四人南'
}

game_state_mapping = {
    GameState.uncompleted: '未完成',
    GameState.completed: '已完成',
    GameState.invalid_total_point: '分数冲突'
}

season_state_mapping = {
    SeasonState.initial: '未开始',
    SeasonState.running: '进行中',
    SeasonState.finished: '已结束'
}

wind_mapping = {
    Wind.east: '东',
    Wind.south: '南',
    Wind.west: '西',
    Wind.north: '北'
}

digit_mapping = {
    1: '一',
    2: '二',
    3: '三',
    4: '四',
}

datetime_format = '%Y-%m-%d %H:%M'
