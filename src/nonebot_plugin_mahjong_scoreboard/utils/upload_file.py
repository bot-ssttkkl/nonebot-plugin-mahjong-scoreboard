from nonebot import require

require("nonebot_plugin_gocqhttp_cross_machine_upload_file")

from nonebot_plugin_gocqhttp_cross_machine_upload_file import upload_group_file, upload_private_file

__all__ = ("upload_group_file", "upload_private_file",)
