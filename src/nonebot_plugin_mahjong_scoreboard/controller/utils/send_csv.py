import csv
from pathlib import Path
from typing import TextIO

from nonebot import require, logger
from nonebot.internal.matcher import current_bot, current_event, current_matcher
from ssttkkl_nonebot_utils.platform import platform_func


def try_import() -> bool:
    try:
        from prettytable import PrettyTable
        require("nonebot_plugin_htmlrender")
        require("nonebot_plugin_saa")
        return True
    except Exception as e:
        logger.opt(exception=e).error("请安装 nonebot-plugin-mahjong-scoreboard[htmlrender]")


template_path = str(Path(__file__).parent.parent / "templates")


def pad_row(row, num: int):
    row = [*row]

    while len(row) != num:
        row.append("")

    return row


async def convert_csv_to_pic(f: TextIO) -> bytes:
    from prettytable import PrettyTable
    from nonebot_plugin_htmlrender import template_to_pic

    reader = csv.reader(f)

    rows = []
    column_num = 0
    for row in reader:
        rows.append(row)
        column_num = max(column_num, len(row))

    rows = [pad_row(row, column_num) for row in rows]
    t = PrettyTable(rows[0])
    t.add_rows(rows[1:])

    html = t.get_html_string()
    image = await template_to_pic(
        template_path=template_path,
        template_name="table.html",
        templates={"body": html},
        pages={"viewport": {"width": column_num * 100, "height": 10}})
    return image


async def send_csv(f: TextIO, filename: str):
    bot = current_bot.get()
    event = current_event.get()
    matcher = current_matcher.get()
    if platform_func.is_supported(bot, "upload_file"):
        data = f.read().encode("utf_8_sig")
        await platform_func(bot).upload_file(bot, event, filename, data)
    else:
        if not try_import():
            await matcher.send("请安装 nonebot-plugin-mahjong-scoreboard[htmlrender]")
        else:
            from nonebot_plugin_saa import MessageFactory, Image

            image = await convert_csv_to_pic(f)
            await MessageFactory(Image(image)).send(reply=True)
