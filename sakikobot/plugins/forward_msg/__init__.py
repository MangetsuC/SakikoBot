from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from nonebot import get_bot, on_message, on_keyword, on_command
from nonebot.adapters import Event, Bot
from nonebot.adapters.onebot.v11.message import MessageSegment as onebot11_MessageSegment, Message as onebot11_Message
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="forward_msg",
    description="转发消息生成插件",
    usage="供其他插件调用，但目前不建议打包转发消息",
    config=Config,
)

config = get_plugin_config(Config)
    




