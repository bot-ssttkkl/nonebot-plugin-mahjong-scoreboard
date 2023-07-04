from nonebot import MatcherGroup, Bot

SUPPORTED_BOT_TYPE = ["OneBot V11", "QQ Guild"]


def _is_bot_supported(bot: Bot):
    return bot.type in SUPPORTED_BOT_TYPE


matcher_group = MatcherGroup(rule=_is_bot_supported)
