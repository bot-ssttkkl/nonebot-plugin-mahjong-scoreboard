from .func_registry import func

try:
    from nonebot.adapters.onebot.v11 import Bot as OneBotV11Bot
    from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
    from nonebot_plugin_gocqhttp_cross_machine_upload_file import upload_file as onebot_v11_upload_file

    func.register(OneBotV11Adapter.get_name(), "upload_file", onebot_v11_upload_file)
except ImportError:
    pass
