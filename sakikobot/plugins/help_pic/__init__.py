from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

from nonebot import on_command, CommandGroup
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg, ArgPlainText
from nonebot.adapters.onebot.v11.message import MessageSegment as onebot11_MessageSegment, Message as onebot11_Message

from typing import Annotated

from .draw import load_font, set_font_size, txt_draw, img_stack, img_to_BytesIO

__plugin_meta__ = PluginMetadata(
    name="help_pic",
    description="借助TOML格式的help文件与PIL库生成插件的帮助图片",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
config.check_font()

l_size = config.help_large_font_size
m_size = config.help_medium_font_size
s_size = config.help_small_font_size

base_font = load_font(config.help_font_path)

cmd_help = on_command('help')

@cmd_help.handle()
async def p_help(arg_msg: Annotated[Message, CommandArg()]):
    if arg := arg_msg.extract_plain_text():
        pass
    else:
        tmp = img_stack([txt_draw('插件：help', set_font_size(base_font, l_size)),
                 txt_draw('本插件的目的是以图形方式展示插件的帮助文档', set_font_size(base_font, m_size)),
                 txt_draw('/help [plugin_name]', set_font_size(base_font, s_size)),
                 txt_draw('该指令用于展示指定插件的帮助文档，plugin_name可选，如果没有设定plugin_name值则展示本插件文档', set_font_size(base_font, s_size)),
                 txt_draw('todo', set_font_size(base_font, s_size)),
                 txt_draw('实际上文档的解析、插件的读取都还没有做，因此只能展示这张图片而已', set_font_size(base_font, s_size))])
        await cmd_help.finish(onebot11_MessageSegment.image(img_to_BytesIO(tmp)))
