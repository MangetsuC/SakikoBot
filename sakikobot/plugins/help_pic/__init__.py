from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

from nonebot import on_command, CommandGroup
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg, ArgPlainText
from nonebot.adapters.onebot.v11.message import MessageSegment as onebot11_MessageSegment, Message as onebot11_Message
from nonebot.plugin import get_available_plugin_names, get_plugin, get_loaded_plugins

from typing import Annotated

import os

from .draw import load_font, set_font_size, txt_draw, img_stack_v, img_stack_h, img_to_BytesIO
from .md2img import Markdown_decoder

__plugin_meta__ = PluginMetadata(
    name="help_pic",
    description="以图片方式发送插件的readme文档",
    usage="用于查看插件的帮助文档，使用/help来获得更详细的说明",
    config=Config,
)

config = get_plugin_config(Config)

#tmpp = get_loaded_plugins() #获取全部加载的插件，name是插件名, module_name是插件全名称(含.)

l_size = config.help_large_font_size
m_size = config.help_medium_font_size
s_size = config.help_small_font_size

base_font = load_font(config.help_font_path)

def generate_txt_help(metadata: PluginMetadata) -> str:
    return f'插件:{metadata.name}\n{metadata.description}\n用途:{metadata.usage}'

cmd_help = on_command('help')

@cmd_help.handle()
async def p_help(arg_msg: Annotated[Message, CommandArg()]) -> None:
    plugins = get_loaded_plugins()
    if arg := arg_msg.extract_plain_text():
        t_p_name = arg.strip(' ')
    else:
        t_p_name = 'help_pic'

    for p in plugins:
        if p.name == t_p_name:
            readme_path = f'./{"/".join([x for x in p.module_name.split(".") if x])}/readme.md'
            if os.path.exists(readme_path):
                tmp = Markdown_decoder.load(readme_path, base_font).build(align='left')
                await cmd_help.finish(onebot11_MessageSegment.image(img_to_BytesIO(tmp)))
            else:
                await cmd_help.finish(generate_txt_help(p.metadata))
    await cmd_help.finish(f'好像没有安装插件{t_p_name}……')


cmd_list = on_command('help.list')

@cmd_list.handle()
async def p_list() -> None:
    plugins = get_loaded_plugins()
    p_txt = []
    for p in plugins:
        this_dsp = p.metadata.description
        if this_dsp:
            p_txt.append(f'{p.name}:{p.metadata.description}')
        else:
            p_txt.append(f'{p.name}')

    p_txt = "\n".join(p_txt)
    await cmd_list.finish(f'当前安装的插件有：\n{p_txt}')


