from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

from nonebot import on_keyword, on_message, on_command, CommandGroup, require, get_bot
from nonebot.adapters import Event, Message
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment as onebot11_MessageSegment, Message as onebot11_Message
from nonebot.adapters.onebot.v11.bot import Bot as onebot11_Bot
from nonebot.typing import T_State
from nonebot.params import CommandArg, ArgPlainText
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.log import logger

from typing import Annotated
import feedparser, toml, threading
from os import path

from .subs import Users_subs, check_to_do
from .url_functions import get_entries_title, get_parser

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

require("args_decoder")
from sakikobot.plugins.args_decoder import args_decode

__plugin_meta__ = PluginMetadata(
    name="anime_subs",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

subs_data_root_path = './devconfig/anime_subs'

users_subs = Users_subs(subs_data_root_path)

n_t = threading.Thread(target = check_to_do, args=(users_subs, ))
n_t.setDaemon(True)
n_t.start()

check_interval_minutes = 10


group = CommandGroup("anisub", prefix_aliases=True, priority=10)

cmd_new = group.command('subs', aliases={"new", "订阅", "新建"})

@cmd_new.handle()
async def subs_new(matcher: Matcher, state: T_State, event: PrivateMessageEvent | GroupMessageEvent, entry_msg: Annotated[Message, CommandArg()]) -> None:
    #立即写入文件
    private_id = 0
    group_id = 0
    
    if isinstance(event, PrivateMessageEvent):
        private_id: int = event.user_id
        user_id = private_id
        users_subs.add_private_user(private_id)
        marked_id = f'private_{private_id}'
    elif isinstance(event, GroupMessageEvent):
        group_id: int = event.group_id
        user_id: int = event.user_id
        users_subs.add_group_user(group_id)
        marked_id = f'group_{group_id}'
    else:
        await cmd_new.finish()

    state['marked_id'] = marked_id
    state['user_id'] = user_id

    if entry_txt := entry_msg.extract_plain_text():
        try:
            entry_data: list[str | list] = args_decode(entry_txt)
        except ValueError as e:
            cmd_new.finish(e.args[0])

        len_data = len(entry_data)
        state['sub_step'] = len_data

        if len_data < 4:
            await cmd_new.send('您可以输入 .exit() 或 .放弃() 来终止订阅流程')

        if len_data == 1:
            state['entry_name'] = entry_data[0]
            await cmd_new.send('请输入rss订阅链接')
        elif len_data == 2:
            state['entry_name'] = entry_data[0]
            state['url'] = entry_data[1]
            state['parser'] = get_parser(state['url'])
            await cmd_new.send('请输入必须包含的检索关键词，输入 .no() 表示没有限制')
        elif len_data == 3:
            state['entry_name'] = entry_data[0]
            state['url'] = entry_data[1]
            state['parser'] = get_parser(state['url'])
            state['must_include'] = entry_data[2]
            await cmd_new.send('请输入必须不包含的检索关键词，输入 .no() 表示没有限制')
        else:
            state['entry_name'] = entry_data[0]
            state['url'] = entry_data[1]
            #state['parser'] = get_parser(state['url'])
            state['must_include'] = entry_data[2]
            state['no_include'] = entry_data[3]
            matcher.set_arg("rest_entry", entry_msg)
    else:
        state['sub_step'] = 0
        await cmd_new.send('请输入订阅名称')

@cmd_new.got('rest_entry')
async def complete_entry(state: T_State, rest_entry: Annotated[str, ArgPlainText()]) -> None: 
    if rest_entry.strip(' ') == '.exit()' or rest_entry.strip(' ') == '.放弃()':
        await cmd_new.finish('已终止订阅流程！')

    if state['sub_step'] == 0:
        state['entry_name'] = rest_entry
        state['sub_step'] = 1
        await cmd_new.reject('请输入rss订阅链接')

    elif state['sub_step'] == 1:
        #获取rss url
        state['url'] = rest_entry
        state['parser'] = get_parser(rest_entry)
        state['sub_step'] = 2
        matced_titles_txt = '\n'.join(get_entries_title(state['parser'], [], [], 10))
        await cmd_new.send(f'目前可以检索到以下条目:\n{matced_titles_txt}')
        await cmd_new.reject('请输入必须包含的检索关键词，输入 .no() 表示没有限制')

    elif state['sub_step'] == 2:
        #获取必须包含的关键词，返回检索列表便于修改
        if rest_entry.strip(' ') == '.确认()':
            state['sub_step'] = 3
            await cmd_new.reject('请输入必须不包含的检索关键词，输入 .no() 表示没有限制')

        if rest_entry.strip(' ') == '.no()':
            tmp = []
        else:
            tmp = [x for x in rest_entry.split(' ') if x]
        state['must_include'] = tmp
        matced_titles_txt = '\n'.join(get_entries_title(state['parser'], tmp, [], 10))
        await cmd_new.send(f'目前可以检索到以下条目:\n{matced_titles_txt}')
        await cmd_new.reject(f'输入 .确认() 来确认必须包含的关键词，您也可以重新输入。当前必须包含的关键词为{" ".join(tmp)}')

    elif state['sub_step'] == 3:
        #获取必须不包含的关键词，返回检索列表便于修改
        if rest_entry.strip(' ') == '.确认()':
            #state['sub_step'] = 4
            users_subs.add_user(state['marked_id'])
            if users_subs.new_sub_entry(state['user_id'], 
                                     state['marked_id'], state['entry_name'], state['url'], state['must_include'], state['no_include'], at_users=[state['user_id']]):

            #写入本地文件
                users_subs.users_dumps()
                users_subs.subs_data_dumps(state['marked_id'])

                await cmd_new.finish(f'订阅{state["entry_name"]}成功')
            await cmd_new.finish(f'条目{state["entry_name"]}已经存在了')
        
        if rest_entry.strip(' ') == '.no()':
            tmp = []
        else:
            tmp = [x for x in rest_entry.split(' ') if x]
        state['no_include'] = tmp
        matced_titles_txt = '\n'.join(get_entries_title(state['parser'], state["must_include"], tmp, 10))
        await cmd_new.send(f'目前可以检索到以下条目:\n{matced_titles_txt}')
        await cmd_new.reject(f'输入 .确认() 来确认必须不包含的关键词，您也可以重新输入。当前必须不包含的关键词为{" ".join(tmp)}')

    elif state['sub_step'] >= 4:
        users_subs.add_user(state['marked_id'])
        if users_subs.new_sub_entry(state['user_id'], 
                                 state['marked_id'], state['entry_name'], state['url'], state['must_include'], state['no_include'], at_users=[state['user_id']]):

        #写入本地文件
            users_subs.users_dumps()
            users_subs.subs_data_dumps(state['marked_id'])

            await cmd_new.finish(f'订阅{state["entry_name"]}成功')
        await cmd_new.finish(f'条目{state["entry_name"]}已经存在了')
    

cmd_add_at = group.command('addat', aliases={"提醒", "atme"})

@cmd_add_at.handle()
async def add_at_group(event: GroupMessageEvent, entry_msg: Annotated[Message, CommandArg()]) -> None:
    #立即写入文件
    if entry_txt := entry_msg.extract_plain_text():
        entry_txt = entry_txt.strip(' ')
        if users_subs.add_at_user(f'group_{event.group_id}', entry_txt, [event.user_id]):
            await cmd_add_at.finish(onebot11_Message([onebot11_MessageSegment.reply(event.message_id), onebot11_MessageSegment.text(f'下次{entry_txt}更新时将提醒您！')]))
        else:
            await cmd_add_at.finish(onebot11_Message([onebot11_MessageSegment.reply(event.message_id), onebot11_MessageSegment.text(f'没有叫做{entry_txt}的订阅……')]))
    await cmd_add_at.finish(onebot11_Message([onebot11_MessageSegment.reply(event.message_id), onebot11_MessageSegment.text('请输入订阅的名称！可以用/anisub.list查看全部订阅名称')]))
    

cmd_list = group.command('list', aliases={"查看全部订阅"})

@cmd_list.handle()
async def list_all_subs(event: Event) -> None:
    if isinstance(event, PrivateMessageEvent):
        event: PrivateMessageEvent
        subs_list = users_subs.get_sub_entries_name(Users_subs.to_private_str(event.user_id))
        if subs_list:
            subs_txt = '\n'.join(subs_list)
            await cmd_list.finish(f'您订阅了：\n{subs_txt}')
        await cmd_list.finish('您还什么都没有订阅哦')

    elif isinstance(event, GroupMessageEvent):
        event: GroupMessageEvent
        subs_list = users_subs.get_sub_entries_name(Users_subs.to_group_str(event.group_id))
        if subs_list:
            subs_txt = '\n'.join(subs_list)
            await cmd_list.finish(f'本群订阅了：\n{subs_txt}')
        await cmd_list.finish('本群还什么都没有订阅哦')
    else:
        await cmd_list.finish()

cmd_del = group.command('del', aliases={"删除"})

@cmd_del.handle()
async def del_sub(event: Event, entry_msg: Annotated[Message, CommandArg()]):
    #立即写入文件
    user_id = event.user_id
    if isinstance(event, PrivateMessageEvent):
        event: PrivateMessageEvent
        marked_id = Users_subs.to_private_str(event.user_id)

    elif isinstance(event, GroupMessageEvent):
        event: GroupMessageEvent
        marked_id = Users_subs.to_group_str(event.group_id)

    else:
        await cmd_list.finish()

    if entry_txt := entry_msg.extract_plain_text():
        check_r = users_subs.check_sub_owner(user_id, marked_id, entry_txt.strip(' '))
        if check_r == 0:
            if users_subs.del_entry(marked_id, entry_txt.strip(' ')):
                users_subs.subs_data_dumps(marked_id)
                await cmd_list.finish(f'订阅{entry_txt}已删除')
            #await cmd_list.finish(f'没有叫做{entry_txt}的订阅条目')
        elif check_r > 0:
            await cmd_list.finish(onebot11_Message([onebot11_MessageSegment.text('您不是该订阅的拥有者，请让'), 
                                                   onebot11_MessageSegment.at(check_r), 
                                                   onebot11_MessageSegment.text('来操作删除')]))
        await cmd_list.finish(f'没有叫做{entry_txt}的订阅条目')

    await cmd_list.finish('请输入订阅名称！')


cmd_clear_group = group.command('cleargroup', aliases={"删除全部群订阅"}, permission=SUPERUSER)

@cmd_clear_group.handle()
async def clear_sub_group(event: GroupMessageEvent, entry_msg: Annotated[Message, CommandArg()]):
    #不会立即写入文件
    if entry_txt := entry_msg.extract_plain_text():
        if entry_txt == '我确定要这样做' or entry_txt == 'Yes sure':
            users_subs.del_group_user(event.group_id)
            await cmd_clear_group.finish(f'所有订阅已清空！')
    await cmd_clear_group.finish('请在指令后添加参数 我确定要这样做 或 Yes sure 来执行此操作')


cmd_clear_private = group.command('clearme', aliases={"删除全部个人订阅"})
    
@cmd_clear_private.handle()
async def clear_sub(event: PrivateMessageEvent, entry_msg: Annotated[Message, CommandArg()]):
    #不会立即写入文件
    if entry_txt := entry_msg.extract_plain_text():
        if entry_txt == '我确定要这样做' or entry_txt == 'Yes sure':
            users_subs.del_private_user(event.user_id)
            await cmd_clear_private.finish(f'所有订阅已清空！')
    await cmd_clear_private.finish('请在指令后添加参数 我确定要这样做 或 Yes sure 来执行此操作')


cmd_push = group.command('push', aliases={"推送"}, rule=to_me(), permission=SUPERUSER)
@cmd_push.handle()
async def anime_test() -> None:
    await push_all_subs(users_subs)


@scheduler.scheduled_job('interval', minutes = check_interval_minutes, id = 'anisub_check', args=[users_subs])
async def push_all_subs(subs: Users_subs) -> None:
    #立即写入上报过的条目
    bot: onebot11_Bot = get_bot()
    subs.del_nodata_users()
    subs.users_dumps() #写入删除的用户
    subs.del_outdated_file()
    
    while subs.private_to_do:
        id = subs.private_to_do.pop()
        msg_data = subs.private_msg_to_do[id]
        for m in msg_data:
            logger.info(f'推送用户{id}订阅的{m}')
            subs_name = m['subs_name'] #订阅条目的名称
            entries = m['new_entries'] #rss获取资源的名称与下载地址，依次排列
            entries_txt = '\n'.join(entries)
            msg = onebot11_MessageSegment.text(f'您的订阅[{subs_name}]有更新！\n{entries_txt}')
            await bot.send_private_msg(user_id=id, message=msg)

            entries_title = []
            entries_url = []
            for i in range(0, len(entries), 2):
                entries_title.append(entries[i])
                entries_url.append(entries[i+1])
            subs.add_reported_entry(Users_subs.to_private_str(id), subs_name, entries_title, entries_url)
        subs.subs_data_dumps(Users_subs.to_private_str(id))

    while subs.group_to_do:
        id = subs.group_to_do.pop()
        msg_data = subs.group_msg_to_do[id]
        for m in msg_data:
            logger.info(f'推送群{id}订阅的{m}')
            subs_name = m['subs_name'] #订阅条目的名称
            entries = m['new_entries'] #rss获取资源的名称与下载地址，依次排列
            entries_txt = '\n'.join(entries)
            msg = []
            for at_id in m['at_users']:
                msg.append(onebot11_MessageSegment.at(at_id))
            msg.append(onebot11_MessageSegment.text(f'\n订阅[{subs_name}]有更新！\n{entries_txt}'))
            await bot.send_group_msg(group_id=id, message=msg)

            entries_title = []
            entries_url = []
            for i in range(0, len(entries), 2):
                entries_title.append(entries[i])
                entries_url.append(entries[i+1])
            subs.add_reported_entry(Users_subs.to_group_str(id), subs_name, entries_title, entries_url)
        subs.subs_data_dumps(Users_subs.to_group_str(id))

    subs.reload_subs_data()
    subs.todo_clear()

    n_t = threading.Thread(target = check_to_do, args=(subs, ))
    n_t.setDaemon(True)
    n_t.start()












