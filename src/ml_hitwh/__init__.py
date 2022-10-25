from nonebot.plugin import PluginMetadata

from . import controller

__plugin_meta__ = PluginMetadata(
    name='您的插件名称（有别于nonebot-plugin-xxx的包名）',
    description='您的简单插件描述',
    usage='''您想在使用命令/help <your plugin package name>时提供的帮助文本''',
    extra={'version': '0.1.0'}
)
