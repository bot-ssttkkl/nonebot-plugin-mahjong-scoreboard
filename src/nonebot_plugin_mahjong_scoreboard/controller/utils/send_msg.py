from nonebot import require
from nonebot.internal.matcher import current_matcher, current_bot, current_event
from ssttkkl_nonebot_utils.platform import platform_func

from ...config import conf

if conf.mahjong_scoreboard_send_image:
    try:
        require("nonebot_plugin_htmlrender")
        require("nonebot_plugin_saa")
    except Exception as e:
        raise Exception("请安装 nonebot-plugin-mahjong-scoreboard[htmlrender]") from e


async def send_msg(*msg: str):
    matcher = current_matcher.get()
    if not conf.mahjong_scoreboard_send_image:
        if conf.mahjong_scoreboard_send_forward_message:
            bot = current_bot.get()
            event = current_event.get()
            await platform_func(bot).send_msgs(bot, event, msg)
        else:
            for s in msg:
                await matcher.send(s)
    else:
        from nonebot_plugin_htmlrender import text_to_pic
        from nonebot_plugin_saa import MessageFactory, Image

        image = await text_to_pic(text="\n\n".join(msg))

        await MessageFactory(Image(image)).send(reply=True)
