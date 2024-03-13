from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from nonebot import on_keyword, on_message, on_command, CommandGroup, require, get_bot
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg, ArgPlainText

from typing import Annotated

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="args_decoder",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)


def args_decode_bracket(args: str) -> list:
    args = args.replace('（', '(').replace('）',')')
    bracket_no = []
    is_left_detect = False
    for i in range(len(args)):
        if (args[i] == '(') and (not is_left_detect):
            bracket_no.append(i)
            is_left_detect = True
        elif (args[i] == ')') and (is_left_detect):
            bracket_no.append(i)
            is_left_detect = False

    if len(bracket_no) % 2 != 0:
        raise ValueError('括号不封闭！')

    origin_data: dict[str, str] = dict()
    if bracket_no:
        for i in range(0, len(bracket_no), 2):
            origin_data[f'%ori{i}iro%'] = args[bracket_no[i]: bracket_no[i + 1] + 1]

        for key in origin_data:
            args = args.replace(origin_data[key], key, 1)

    entry_data: list[str | list] = [x for x in args.split(' ') if x]

    for i in range(len(entry_data)):
        if entry_data[i] in origin_data:
            entry_data[i] = [x for x in origin_data[entry_data[i]].strip('()').split(' ') if x]

    return entry_data

def args_decode_quotation(args: str) -> list:
    args = args.replace('“', '\'').replace('”','\'').replace('’', '\'').replace('‘','\'').replace('"', '\'')
    bracket_no = []
    is_left_detect = False
    for i in range(len(args)):
        if args[i] == '\'':
            if not is_left_detect:
                bracket_no.append(i)
                is_left_detect = True
            elif is_left_detect:
                bracket_no.append(i)
                is_left_detect = False

    if len(bracket_no) % 2 != 0:
        raise ValueError('引号不封闭！')

    origin_data: dict[str, str] = dict()
    if bracket_no:
        for i in range(0, len(bracket_no), 2):
            origin_data[f'%ori{i}iro%'] = args[bracket_no[i]: bracket_no[i + 1] + 1]

        for key in origin_data:
            args = args.replace(origin_data[key], key, 1)

    entry_data: list[str | list] = [x for x in args.split(' ') if x]

    for i in range(len(entry_data)):
        if entry_data[i] in origin_data:
            entry_data[i] = [x for x in origin_data[entry_data[i]].strip('\'').split(' ') if x]

    return entry_data

def args_decode_none(args: str) -> list:
    return [x for x in args.split(' ') if x]

def args_decode(args: str) -> list:
    if args:
        type = tell_type(args)
        if type == 'quotation':
            return args_decode_quotation(args)
        elif type == 'bracket':
            return args_decode_bracket(args)
        else:
            return args_decode_none(args)
        
    return []

def tell_type(args: str) -> str:
    if any(x in args for x in ['\'', '"', '“', '‘', '”', '’']):
        return 'quotation'
    elif any(x in args for x in ['（', '(', ') ', ')']):
        return 'bracket'
    
    return ''

decoder_test = on_command('decode.test')

@decoder_test.handle()
async def decode(args_msg: Annotated[Message, CommandArg()]) -> None:
    if txt := args_msg.extract_plain_text():
        try:
            await decoder_test.finish(str(args_decode(txt)))
        except ValueError as e:
            await decoder_test.finish(e.args[0])

    await decoder_test.finish('字符串不包含需要解析的内容！')


