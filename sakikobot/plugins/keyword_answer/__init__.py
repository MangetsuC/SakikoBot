from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from nonebot import on_message, CommandGroup, require
from nonebot.log import logger
from nonebot.adapters import Message
from nonebot.params import Keyword, CommandArg, ArgPlainText
from nonebot.rule import KeywordsRule, to_me
from nonebot.internal.rule import Rule
from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER

from .config import Config
from .lexicon_functions import Lexicon

from typing import Annotated

from os import path

require('args_decoder')
from sakikobot.plugins.args_decoder import args_decode

class Updatable_KeywordsRule(KeywordsRule):
    def update(self, new_keywords:list[str]):
        self.keywords = tuple(new_keywords)

__plugin_meta__ = PluginMetadata(
    name="keyword_answer",
    description="基于词库的简单关键词检索回复,酷Q最基础的功能,主要作用是帮助我熟悉插件开发流程",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
lexicon_path = config.keyword_answer_lexicon_path

if not path.exists(lexicon_path):
    #无词库创建空文件
    f = open(lexicon_path, 'w', encoding='utf-8')
    f.close()

lexicon = Lexicon(lexicon_path)

updatable_keywordsrule = Updatable_KeywordsRule()
if config.keyword_answer_enable:
    updatable_keywordsrule.update(lexicon.get_keywords())
else:
    updatable_keywordsrule.update([])
keyword_matcher = on_message(Rule(updatable_keywordsrule), priority=config.keyword_answer_answer_priority)

#关键词响应
@keyword_matcher.handle()
async def answer_function(msg: Annotated[str, Keyword()]) -> None:
    answer_list = lexicon.get_candidate(msg)
    if answer_list:
        answer_txt = answer_list[0]
        await keyword_matcher.finish(answer_txt)

    await keyword_matcher.finish()

#控制指令
group = CommandGroup("lexi", prefix_aliases=True, priority=config.keyword_answer_command_priority)
cmd_reload = group.command('reload', rule=to_me(), aliases={"刷新词库"}, permission=SUPERUSER)

@cmd_reload.handle()
async def reload_lexicon() -> None:
    '重新加载词库'
    lexicon.reload()
    if config.keyword_answer_enable:
        rule_to_del = keyword_matcher.rule
        updatable_keywordsrule.update(lexicon.get_keywords())
        keyword_matcher.rule = Rule(updatable_keywordsrule)
        try:
            del rule_to_del
        except BaseException:
            pass
        await cmd_dumps.finish('词库已重新加载')
    await cmd_dumps.finish('词库已重新加载，但自动回复已禁用')

cmd_dumps = group.command('dumps', rule=to_me(), aliases={"dump", "写入词库"}, permission=SUPERUSER)

@cmd_dumps.handle()
async def dumps_lexicon() -> None:
    lexicon.dumps_keyword_answer_lexicon()
    await cmd_dumps.finish('词库文件已写入')

cmd_new = group.command('new', rule=to_me(), aliases={"新建词条"}, permission=SUPERUSER)

@cmd_new.handle()
async def new_lexicon(state: T_State, entry_msg: Annotated[Message, CommandArg()]) -> None:
    if entry_txt := entry_msg.extract_plain_text():
        try:
            entry_list: list[str | list] = args_decode(entry_txt)
        except ValueError as e:
            cmd_new.finish(e.args[0])
        #entry_list = entry_txt.split('[s]')
        len_entry_list = len(entry_list)
        if len_entry_list == 1:
            entry_name : str = entry_list[0].strip('\'\"')
            state['entry_num'] = 1
            state['entry_name'] = entry_name
            await cmd_new.send('请输入关键词')

        elif len_entry_list == 2:
            entry_name : str = entry_list[0].strip('\'\"')
            if isinstance(entry_list[1], str):
                entry_list[1] = [].append(entry_list[1])
            entry_keywords : list[str] = entry_list[1]
            state['entry_num'] = 2
            state['entry_name'] = entry_name
            state['entry_keywords'] = entry_keywords
            await cmd_new.send('请输入回复词')

        else:
            entry_name : str = entry_list[0].strip('\'\"')
            if isinstance(entry_list[1], str):
                entry_list[1] = [].append(entry_list[1])
            if isinstance(entry_list[2], str):
                entry_list[2] = [].append(entry_list[2])
            entry_keywords : list[str] = entry_list[1]
            entry_answers : list[str] = entry_list[2]

            lexicon.new_keyword_answer_group(entry_name, entry_keywords, entry_answers)
            await reload_lexicon()
            await cmd_new.finish(f'添加成功词条:{entry_name}，使用reload指令来刷新词库，使用dumps指令写入文件')

    else:
        state['entry_num'] = 0
        await cmd_new.send('请输入词条名称')

@cmd_new.got('rest_entry')
async def complete_entry(state: T_State, rest_entry: Annotated[str, ArgPlainText()]) -> None: 
    if rest_entry == '.exit()' or rest_entry == '.放弃()':
        await cmd_new.finish('已终止词条添加')
    elif state['entry_num'] == 0:
        state['entry_name'] = rest_entry.strip('\'\"')
        state['entry_num'] += 1
        await cmd_new.reject('请输入关键词')

    elif state['entry_num'] == 1:
        entry_keywords : list[str] = [x for x in rest_entry.split(' ') if x]
        state['entry_keywords'] = entry_keywords
        state['entry_num'] += 1
        await cmd_new.reject('请输入回复词')

    elif state['entry_num'] == 2:
        entry_answers : list[str] = [x for x in rest_entry.split(' ') if x]
        lexicon.new_keyword_answer_group(state['entry_name'], state['entry_keywords'], entry_answers)
        await cmd_new.finish(f'添加成功词条:{state["entry_name"]}，使用reload指令来刷新词库，使用dumps指令写入文件')

    else:
        await cmd_new.finish(f'词条添加失败了！')

cmd_del = group.command('del', rule=to_me(), aliases={"删除词条"}, permission=SUPERUSER)

@cmd_del.handle()
async def del_lexicon(matcher: Matcher, key_name_msg: Annotated[Message, CommandArg()]) -> None:
    if key_name_msg.extract_plain_text():
        matcher.set_arg('key_name', key_name_msg)

@cmd_del.got('key_name', prompt='请输入要删除的词条名称')
async def complete_del(key_name: Annotated[str, ArgPlainText()]):
    if lexicon.delete_candidate(key_name):
        await cmd_del.finish(f'词条:{key_name}已被删除，使用reload来重新加载词库，使用dumps来写入词库')
    else:
        await cmd_del.finish(f'词条:{key_name}不存在')

cmd_list = group.command('list', rule=to_me(), aliases={"列举词条"}, permission=SUPERUSER)

@cmd_list.handle()
async def list_lexicon(page_no_msg: Annotated[Message, CommandArg()], page_num_msg: Annotated[Message, CommandArg()]) -> None:
    page_no_int = 1
    if page_no := page_no_msg.extract_plain_text():
        if page_no.isdigit():
            page_no_int = int(page_no)

    page_num_int = 5
    if page_num := page_num_msg.extract_plain_text():
        if page_num.isdigit():
            page_num_int = int(page_num)

    real_num_int, ans_list = lexicon.candidate_print((page_no_int - 1) * page_num_int + 1, page_no_int * page_num_int)

    await cmd_list.send(f'当前展示第{page_no_int}页的{real_num_int}条结果')

    for i in ans_list:
        await cmd_list.send(i)

    await cmd_list.finish()

cmd_show = group.command('show', rule=to_me(), aliases={"查看词条"}, permission=SUPERUSER)

@cmd_show.handle()
async def show_candidate(matcher: Matcher, key_name_msg: Annotated[Message, CommandArg()]) -> None:
    if key_name_msg.extract_plain_text():
        matcher.set_arg('key_name', key_name_msg)

@cmd_show.got('key_name', prompt='请输入词条名称')
async def complete_show(key_name: Annotated[str, ArgPlainText()]):
    await cmd_show.finish(lexicon.candidate_str(key_name))





