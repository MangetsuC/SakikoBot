from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

from nonebot import on_command, CommandGroup
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg, ArgPlainText
from nonebot.adapters.onebot.v11.message import MessageSegment as onebot11_MessageSegment, Message as onebot11_Message
from nonebot.plugin import get_available_plugin_names, get_plugin, get_loaded_plugins

from typing import Annotated

from .draw import load_font, set_font_size, txt_draw, img_stack_v, img_stack_h, img_to_BytesIO
from .md2img import Markdown_decoder

__plugin_meta__ = PluginMetadata(
    name="help_pic",
    description="借助TOML格式的help文件与PIL库生成插件的帮助图片",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
config.check_font()

#tmpp = get_loaded_plugins() #获取全部加载的插件，name是插件名, module_name是插件全名称(含.)

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
        tmp = Markdown_decoder.load('./devconfig/test_readme.md', base_font).build()

        await cmd_help.finish(onebot11_MessageSegment.image(img_to_BytesIO(tmp)))
