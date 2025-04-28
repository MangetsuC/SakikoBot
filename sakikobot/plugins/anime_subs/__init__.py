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
from .url_functions import get_entries_title, get_parser, get_possible_episode, get_most_possible_episode
from .bgm_get import get_episodes as bgm_get_episodes, get_image as bgm_get_image, get_subject_id_from_keyword as bgm_get_subject_id_from_keyword
from .poster_draw import open_bytes_PIL as poster_open_bytes_PIL, draw_squre_poster2, img_to_BytesIO as poster_img_to_BytesIO

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

require("args_decoder")
from sakikobot.plugins.args_decoder import args_decode

__plugin_meta__ = PluginMetadata(
    name="anime_subs",
    description="番剧订阅插件",
    usage="使用/anisub.new来订阅番剧rss资源，使用/anisub.del来删除不需要的订阅，使用/anisub.atme来添加提醒",
    config=Config,
)

config = get_plugin_config(Config)

subs_data_root_path = config.subs_data_root_path

users_subs = Users_subs(subs_data_root_path)

font_set_normal = {'path': config.font_normal_path, 'size': config.font_normal_size}
font_set_small = {'path': config.font_small_path, 'size': config.font_small_size}

n_t = threading.Thread(target = check_to_do, args=(users_subs, ))
n_t.setDaemon(True)
n_t.start()

check_interval_minutes = config.check_interval_minutes


group = CommandGroup("anisub", prefix_aliases=True, priority=10)

cmd_new = group.command('subs', aliases={"new", "add", "订阅", "新建"})

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
async def list_all_subs(event: Event, option: Annotated[Message, CommandArg()]) -> None:
    is_archived_show = False
    if option_txt := option.extract_plain_text().strip():
        if option_txt == 'all' or option_txt == '全部':
            is_archived_show = True

    if isinstance(event, PrivateMessageEvent):
        event: PrivateMessageEvent
        subs_list = users_subs.get_sub_entries_name(Users_subs.to_private_str(event.user_id), is_archived_show)
        if subs_list:
            subs_txt = '\n'.join(subs_list)
            await cmd_list.finish(f'您订阅了：\n{subs_txt}')
        await cmd_list.finish('您还什么都没有订阅哦')

    elif isinstance(event, GroupMessageEvent):
        event: GroupMessageEvent
        subs_list = users_subs.get_sub_entries_name(Users_subs.to_group_str(event.group_id), is_archived_show)
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
        elif check_r > 0:
            await cmd_list.finish(onebot11_Message([onebot11_MessageSegment.text('您不是该订阅的拥有者，请让'), 
                                                   onebot11_MessageSegment.at(check_r), 
                                                   onebot11_MessageSegment.text('来操作删除')]))
        await cmd_list.finish(f'没有叫做{entry_txt}的订阅条目')

    await cmd_list.finish('请输入订阅名称！')

cmd_get = group.command('get', aliases={"下载"})

@cmd_get.handle()
async def get_sub(event: Event, entry_msg: Annotated[Message, CommandArg()]):

    def reply_Message(event_id: int, txt: str) -> onebot11_Message:
        return onebot11_Message([onebot11_MessageSegment.reply(event_id), onebot11_MessageSegment.text(txt)])

    #查询已经记录的剧集对应的链接
    if isinstance(event, PrivateMessageEvent):
        event: PrivateMessageEvent
        marked_id = Users_subs.to_private_str(event.user_id)

    elif isinstance(event, GroupMessageEvent):
        event: GroupMessageEvent
        marked_id = Users_subs.to_group_str(event.group_id)

    else:
        await cmd_get.finish()

    if entry_txt := entry_msg.extract_plain_text():
        args = [x for x in entry_txt.split(' ') if x]

        if len(args) >= 2:
            entry_name = args[0] #订阅名称
            target_episode = args[1]
            if target_episode.isnumeric():
                reported_datas = users_subs.get_reported_urls(marked_id, entry_name)
                if isinstance(reported_datas, dict):
                    eps = int(target_episode)
                    possible_entries = [x for x in reported_datas.keys() if eps in get_possible_episode(x)]
                    if possible_entries:
                        urls = []
                        for each_p_e in possible_entries:
                            t_url = reported_datas[each_p_e]
                            if 'https://' in t_url:
                                t_url = f'{t_url.replace("https://", "")}[前面添加https之类的]'
                            elif 'http://' in t_url:
                                t_url = f'{t_url.replace("http://", "")}[前面添加http之类的]'
                            urls.append(t_url)
                        tmp_msg = '\n'.join([f'{x}\n{y}' for x, y in zip(possible_entries, urls)])
                        await cmd_get.finish(reply_Message(event.message_id, 
                                                            f'您寻找的{entry_name}的第{target_episode}集对应的资源很可能是:\n{tmp_msg}'))
                    else:
                        await cmd_get.finish(reply_Message(event.message_id, f'订阅{entry_name}暂时还没有目标数据'))
                await cmd_get.finish(reply_Message(event.message_id, f'没有叫做{entry_name}的订阅条目哦'))
            else:
                await cmd_get.finish(reply_Message(event.message_id, '请输入正确的集数！'))
        elif args:
            await cmd_get.finish(reply_Message(event.message_id, '请输入目标集数！'))
        else:
            await cmd_get.finish(reply_Message(event.message_id, '参数也许不对吧……'))

    await cmd_get.finish(reply_Message(event.message_id, '请输入订阅名称与目标集数！'))


cmd_info = group.command('info', aliases={"信息"})

@cmd_info.handle()
async def info_get(event: Event, entry_msg: Annotated[Message, CommandArg()]):
    '获取订阅的信息，包括rss订阅地址和关键词'
    if isinstance(event, PrivateMessageEvent):
        event: PrivateMessageEvent
        marked_id = Users_subs.to_private_str(event.user_id)

    elif isinstance(event, GroupMessageEvent):
        event: GroupMessageEvent
        marked_id = Users_subs.to_group_str(event.group_id)

    else:
        await cmd_info.finish()
    
    if entry_txt := entry_msg.extract_plain_text():
        entry_name = entry_txt.strip()
        if marked_id in users_subs.subs_data:
            if entry_name in users_subs.subs_data[marked_id]:
                tmp_url = users_subs.subs_data[marked_id][entry_name]['url']
                base_info = [f'订阅[{entry_name}]的信息如下:\nUrl:{tmp_url}']

                if must_include := users_subs.subs_data[marked_id][entry_name]['must_include']:
                    base_info.append(f'必须包含:{" ".join(must_include)}')

                if no_include := users_subs.subs_data[marked_id][entry_name]['no_include']:
                    base_info.append(f'必须不含:{" ".join(no_include)}')

                await cmd_get.finish('\n'.join(base_info))

        await cmd_get.finish(f'没有叫做{entry_name}的订阅条目哦')

cmd_edit = group.command('edit', aliases={"修改"})
@cmd_edit.handle()
async def edit_sub(event: Event, entry_msg: Annotated[Message, CommandArg()]):
    #修改订阅信息，立即写入
    user_id = event.user_id
    if isinstance(event, PrivateMessageEvent):
        event: PrivateMessageEvent
        marked_id = Users_subs.to_private_str(event.user_id)

    elif isinstance(event, GroupMessageEvent):
        event: GroupMessageEvent
        marked_id = Users_subs.to_group_str(event.group_id)

    else:
        await cmd_edit.finish()

    if entry_txt := entry_msg.extract_plain_text():
        try:
            entry_data: list[str | list] = args_decode(entry_txt)
        except ValueError as e:
            cmd_edit.finish(e.args[0])

        if len(entry_data) >= 3:
            entry_name = entry_data[0] #订阅名称
            old = entry_data[1]
            new = entry_data[2]
        else:
            await cmd_edit.finish('输入信息不完整，参数应为订阅名称 修改项(url/mi/ni) 新值')

        check_r = users_subs.check_sub_owner(user_id, marked_id, entry_name)
        if check_r == 0:
            if old == 'url':
                new_data = dict(url = new)
                old_txt = '订阅链接'
            elif old == 'mi':
                new_data = dict(must_include = new)
                old_txt = '必须包含的关键词'
            elif old == 'ni':
                new_data = dict(no_include = new)
                old_txt = '必须不含的关键词'
            else:
                await cmd_edit.finish('修改项错误，可选值为url/mi/ni，分别代表订阅地址/必须包含/必须不含')

            users_subs.edit_sub(marked_id, entry_name, new_data)
            users_subs.subs_data_dumps(marked_id)
            await cmd_edit.finish(f'订阅[{entry_name}]已更新{old_txt}为{new}')

        elif check_r > 0:
            await cmd_edit.finish(onebot11_Message([onebot11_MessageSegment.text('您不是该订阅的拥有者，请让'), 
                                                   onebot11_MessageSegment.at(check_r), 
                                                   onebot11_MessageSegment.text('来操作修改')]))
        await cmd_edit.finish(f'没有叫做{entry_txt}的订阅条目')

    await cmd_edit.finish('请输入订阅名称！')

cmd_bgm_id_set = group.command('bgm_id')
@cmd_bgm_id_set.handle()
async def set_bgm_id(event: Event, entry_msg: Annotated[Message, CommandArg()]):
    user_id = event.user_id
    if isinstance(event, PrivateMessageEvent):
        event: PrivateMessageEvent
        marked_id = Users_subs.to_private_str(event.user_id)

    elif isinstance(event, GroupMessageEvent):
        event: GroupMessageEvent
        marked_id = Users_subs.to_group_str(event.group_id)
    else:
        await cmd_info.finish()

    if entry_txt := entry_msg.extract_plain_text():
        entry_data = entry_txt.split(' ')
        if len(entry_data) >= 2:
            sub_name = entry_data[0]
            bgm_id: str = entry_data[1]
            if bgm_id.isdigit():
                bgm_id = int(bgm_id)
                if users_subs.set_bgm_id(marked_id, sub_name, bgm_id):
                    await cmd_bgm_id_set.finish(f'订阅{sub_name}已绑定Bangumi ID: {bgm_id}')
                await cmd_bgm_id_set.finish(f'没有找到订阅{sub_name}')
            await cmd_bgm_id_set.finish('Bangumi ID应该是数字')
    await cmd_bgm_id_set.finish('输入参数数目有误')

cmd_archive = group.command('archive', aliases={"归档"})
@cmd_archive.handle()
async def archive_sub(event: Event, entry_msg: Annotated[Message, CommandArg()]):
    if isinstance(event, PrivateMessageEvent):
        event: PrivateMessageEvent
        marked_id = Users_subs.to_private_str(event.user_id)

    elif isinstance(event, GroupMessageEvent):
        event: GroupMessageEvent
        marked_id = Users_subs.to_group_str(event.group_id)

    else:
        await cmd_info.finish()
    
    if entry_txt := entry_msg.extract_plain_text():
        entry_names = entry_txt.split(' ')
        archived_subs_name: list[str] = []
        unfound_subs_name: list[str] = []
        for entry_name in entry_names:
            entry_name = entry_name.strip()
            if marked_id in users_subs.subs_data:
                if entry_name in users_subs.subs_data[marked_id]:
                    users_subs.archive_sub(marked_id, entry_name)
                    archived_subs_name.append(entry_name)
                else:
                    unfound_subs_name.append(entry_name)

        if archived_subs_name != [] and unfound_subs_name != []:
            await cmd_archive.finish(f'订阅[{"、".join(archived_subs_name)}]已经归档了，但是没有叫[{"、".join(unfound_subs_name)}]的订阅。')
        elif archived_subs_name != [] and unfound_subs_name == []:
            await cmd_archive.finish(f'订阅[{"、".join(archived_subs_name)}]已经归档了。')
        elif archived_subs_name == [] and unfound_subs_name != []:
            await cmd_archive.finish(f'没有叫做订阅[{"、".join(archived_subs_name)}]的订阅。')
        else:
            await cmd_archive.finish()


cmd_unarchive = group.command('unarchive', aliases={"取出"})
@cmd_unarchive.handle()
async def unarchive_sub(event: Event, entry_msg: Annotated[Message, CommandArg()]):
    if isinstance(event, PrivateMessageEvent):
        event: PrivateMessageEvent
        marked_id = Users_subs.to_private_str(event.user_id)

    elif isinstance(event, GroupMessageEvent):
        event: GroupMessageEvent
        marked_id = Users_subs.to_group_str(event.group_id)

    else:
        await cmd_info.finish()
    
    if entry_txt := entry_msg.extract_plain_text():
        entry_names = entry_txt.split(' ')
        unarchived_subs_name: list[str] = []
        unfound_subs_name: list[str] = []
        for entry_name in entry_names:
            entry_name = entry_name.strip()
            if marked_id in users_subs.subs_data:
                if entry_name in users_subs.subs_data[marked_id]:
                    users_subs.unarchive_sub(marked_id, entry_name)
                    unarchived_subs_name.append(entry_name)
                else:
                    unfound_subs_name.append(entry_name)
                
        if unarchived_subs_name != [] and unfound_subs_name != []:
            await cmd_archive.finish(f'订阅[{"、".join(unarchived_subs_name)}]已经取出了，但是没有叫[{"、".join(unfound_subs_name)}]的订阅。')
        elif unarchived_subs_name != [] and unfound_subs_name == []:
            await cmd_archive.finish(f'订阅[{"、".join(unarchived_subs_name)}]已经取出了。')
        elif unarchived_subs_name == [] and unfound_subs_name != []:
            await cmd_archive.finish(f'没有叫做订阅[{"、".join(unarchived_subs_name)}]的订阅。')
        else:
            await cmd_archive.finish()

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

    send_function = [bot.send_private_msg, bot.send_group_msg]
    # all_msgs: list[dict] = []

    def dump_to_msgs(function_no: int, user_id: int, msg: onebot11_MessageSegment|list[onebot11_MessageSegment]) -> dict:
        return dict(no = function_no, id = user_id, message = msg)

    while subs.private_to_do != [] or subs.group_to_do != []:
        if subs.private_to_do != []:
            marked_id = subs.private_to_do.pop()
            msg_data = subs.private_msg_to_do[marked_id]
            send_no = 0
            file_marked_id = Users_subs.to_private_str(marked_id)
        else:
            marked_id = subs.group_to_do.pop()
            msg_data = subs.group_msg_to_do[marked_id]
            send_no = 1
            file_marked_id = Users_subs.to_group_str(marked_id)

        for m in msg_data:
            m_msgs = []
            logger.info(f'推送用户{marked_id}订阅的{m}')
            subs_name = m['subs_name'] #订阅条目的名称
            entries = m['new_entries'] #rss获取资源的名称与下载地址，依次排列

            bgm_id = subs.get_bgm_id(file_marked_id, subs_name)
            if bgm_id == None:
                n_bgm_id = bgm_get_subject_id_from_keyword(subs_name)
                if n_bgm_id != None:
                    subs.set_bgm_id(file_marked_id, subs_name, n_bgm_id)
                    bgm_id = n_bgm_id
                

            updated_episode_list: list[str] = []
            unknown_episode_list: list[str] = []
            for i in range(0, len(entries), 2):
                possible_episode = get_most_possible_episode(entries[i])
                if possible_episode != None:
                    updated_episode_list.append(str(possible_episode))
                else:
                    if (i + 1) < len(entries):
                        unknown_episode_list.append(entries[i])
                        unknown_episode_list.append(entries[i + 1])

            additional_unknown_txt = ''
            if updated_episode_list != []:
                additional_unknown_txt = '还'
                updated_episode_list.sort(key=lambda x:int(x))
                updated_episodes = [int(x) for x in updated_episode_list]
                poster_state = False

                exist_epss = []
                reported_urls = subs.get_reported_urls(file_marked_id, subs_name)
                if isinstance(reported_urls, dict):
                    for n in reported_urls.keys():
                        p_eps = get_most_possible_episode(n)
                        if p_eps != None:
                            exist_epss.append(p_eps)
                exist_epss = list(set(exist_epss))

                #仅更新字幕v2版时记录但不推送更新
                is_only_v2: bool = True
                for u_eps in updated_episodes:
                    if u_eps not in exist_epss:
                        is_only_v2 = False

                if not is_only_v2:
                    msg1 = []
                    if send_no == 1:
                        for at_id in m['at_users']:
                            msg1.append(onebot11_MessageSegment.at(at_id))

                    if bgm_id != None:
                        

                        poster_img = bgm_get_image(bgm_id)
                        if poster_img != None:
                            poster_img = poster_open_bytes_PIL(poster_img)
                            total_epss = bgm_get_episodes(bgm_id)
                            if total_epss != None:
                                poster_img = draw_squre_poster2(poster_img, total_epss, updated_episodes, exist_epss, font_set_normal, font_set_small)
                                poster_img_bytes = poster_img_to_BytesIO(poster_img)
                                poster_state = True

                                msg1.append(onebot11_MessageSegment.image(poster_img_bytes))
                                m_msgs.append(dump_to_msgs(send_no, marked_id, msg1))

                    if not poster_state:
                        episode_txt = '、'.join(updated_episode_list)
                        msg1.append(onebot11_MessageSegment.text(f'订阅的[{subs_name}]更新了第{episode_txt}集！'))
                        m_msgs.append(dump_to_msgs(send_no, marked_id, msg1))

            if unknown_episode_list != []:
                entries_txt = '\n'.join(unknown_episode_list)
                msg2 = onebot11_MessageSegment.text(f'订阅的[{subs_name}]{additional_unknown_txt}有一些未知的更新！\n{entries_txt}')
                m_msgs.append(dump_to_msgs(send_no, marked_id, msg2))

            for each_m_msg in m_msgs:
                await send_function[each_m_msg['no']](user_id=each_m_msg['id'], message=each_m_msg['message'])

            entries_title = []
            entries_url = []
            for i in range(0, len(entries), 2):
                if (i + 1) < len(entries):
                    entries_title.append(entries[i])
                    entries_url.append(entries[i+1])
            subs.add_reported_entry(file_marked_id, subs_name, entries_title, entries_url)
        subs.subs_data_dumps(file_marked_id)

    subs.reload_subs_data()
    subs.todo_clear()

    n_t = threading.Thread(target = check_to_do, args=(subs, ))
    n_t.setDaemon(True)
    n_t.start()












