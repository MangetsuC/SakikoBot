from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from nonebot import get_bot, on_keyword, require, CommandGroup
from nonebot.log import logger
from nonebot.adapters import Event

from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment as onebot11_MessageSegment, Message as onebot11_Message

import cv2, threading, os

from .config import Config
from .pics import pic_resize_max, pic_compress_save, pic_noise, download_pics_threading, open_PIL, pic_resize_max_PIL, pic_compress_save_PIL, pic_noise_PIL
from .sese import Sese_logger



__plugin_meta__ = PluginMetadata(
    name="setu",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

pics_path = './devconfig/pics'
pics_path_r18 = './devconfig/pics18'
pics_path_setu = './devconfig/pics_setu'
pics_noise_path = './devconfig/pics_noise'
group_noise_num = 200
interval_time = 30
max_local_pics_num = 10
max_cached_pics_num = min(6, max_local_pics_num)

require('forward_msg')
from sakikobot.plugins.forward_msg.forward_msg_functions import send_forward_msg

sese_logger = Sese_logger(root_path= dict(pixiv = pics_path, r18 = pics_path_r18, setu = pics_path_setu, noise = pics_noise_path), 
                          interval_time= interval_time,
                          proxy=config.setu_proxy)
sese_logger.load_init_cache(max_local_pics_num)
sese_logger.load_init_cache(max_local_pics_num, 'r18')
sese_logger.load_init_cache(max_local_pics_num, 'setu')

#清空噪点图片
for i in os.listdir(pics_noise_path):
    os.remove(f'{pics_noise_path}/{i}')

t_1 = threading.Thread(target= download_pics_threading, args=(sese_logger, max_cached_pics_num))
t_r18 = threading.Thread(target= download_pics_threading, args=(sese_logger, max_cached_pics_num, 'r18'))
t_1.setDaemon(True)
t_r18.setDaemon(True)
t_1.start()
t_r18.start()


def sese_pic_msg_build(cached_pic_data: dict, noise_path: str, is_group: bool) -> list[onebot11_MessageSegment]:
    if pic_path := cached_pic_data.get('path', ''):
        pic_name = cached_pic_data['meta_data']['pic_name']
        real_pic_name = cached_pic_data['meta_data']['real_pic_name']
        pic_pid = cached_pic_data['meta_data'].get('pid', '')
        pic_url = cached_pic_data['meta_data'].get('url', '')

        tmp: list[onebot11_MessageSegment] = []
        if pic_pid:
            tmp.append(onebot11_MessageSegment.text(f'很可能是Pixiv ID'))
            tmp.append(onebot11_MessageSegment.text(pic_pid))

        if not is_group:
            with open (pic_path, 'rb') as file:
                pic_bytes = file.read()
            tmp.append(onebot11_MessageSegment.image(pic_bytes))
        else:
            #tmp_pic = cv2.imread(pic_path)
            #tmp_pic = pic_resize_max(tmp_pic, 1920)
            #tmp_pic = pic_noise(tmp_pic, group_noise_num)
            #pic_compress_save(tmp_pic, f'{noise_path}/{real_pic_name}.jpg')

            tmp_pic = open_PIL(pic_path)
            tmp_pic = pic_resize_max_PIL(tmp_pic, 1920)
            pic_noise_PIL(tmp_pic, group_noise_num)
            pic_compress_save_PIL(tmp_pic, f'{noise_path}/{real_pic_name}.jpg')

            with open (f'{noise_path}/{real_pic_name}.jpg', 'rb') as file:
                pic_bytes = file.read()
            tmp.append(onebot11_MessageSegment.image(pic_bytes))

        if pic_url:
            tmp.append(onebot11_MessageSegment.text(f'图片源地址'))
            tmp.append(onebot11_MessageSegment.text(pic_url))

        return tmp
    return []

sese_matcher = on_keyword(['色色', '色图', '涩涩', '涩图'])

@sese_matcher.handle()
async def sese_timer_update(event: Event) -> None:
    id = 0
    if isinstance(event, GroupMessageEvent):
        event:GroupMessageEvent
        id = event.group_id
    elif isinstance(event, PrivateMessageEvent):
        event:PrivateMessageEvent
        id = event.user_id

    if rest_time:= sese_logger.check_timer_id(id):
        if rest_time < 0:
            await sese_matcher.finish()
        await sese_matcher.finish(f'{rest_time}秒后才能涩涩！')

@sese_matcher.handle()
async def send_setu(event: Event) -> None:
    this_bot = get_bot()

    message_id = event.message_id
    id = 0
    group_id = 0
    private_id = 0
    if isinstance(event, GroupMessageEvent):
        event:GroupMessageEvent
        group_id = event.group_id
        id = group_id
    elif isinstance(event, PrivateMessageEvent):
        event:PrivateMessageEvent
        private_id = event.user_id
        id = private_id
    else:
        sese_matcher.finish()

    d_t = threading.Thread(target= download_pics_threading, args=(sese_logger, max_cached_pics_num))
    d_t.start()

    cached_pic = sese_logger.pics_cache_pop()
    if cached_pic["meta_data"]:
        logger.success(f'从缓存中获取到图片{cached_pic["meta_data"]["pic_name"]}')
    else:
        logger.warning('未能从缓存中获取到图片')

    if needed_msg:= sese_pic_msg_build(cached_pic, pics_noise_path, private_id == 0):
        await send_forward_msg(this_bot, needed_msg, private_id, group_id)

        #消息发送后删除本地文件
        if ori_pic_path := cached_pic.get('path', ''):
            os.remove(ori_pic_path)
            if private_id == 0:
                os.remove(f'{pics_noise_path}/{cached_pic["meta_data"]["real_pic_name"]}.jpg')

            sese_logger.dump_cache()

        await sese_matcher.finish()

    sese_logger.roll_back_time_id(id)
    await sese_matcher.finish(onebot11_Message([onebot11_MessageSegment.reply(message_id), onebot11_MessageSegment.text('图片获取失败了……')]))
    

setu_group = CommandGroup("setu", prefix_aliases=True, priority=10)
cmd_18 = setu_group.command('risk')

@cmd_18.handle()
async def setu18_timer_update():
    if rest_time:= sese_logger.check_timer_18():
        await sese_matcher.finish(f'太涩了，等{rest_time}秒！')

@cmd_18.handle()
async def send_setu18(event: Event):
    this_bot = get_bot()

    message_id = event.message_id
    group_id = 0
    private_id = 0
    if isinstance(event, GroupMessageEvent):
        event:GroupMessageEvent
        group_id = event.group_id
    elif isinstance(event, PrivateMessageEvent):
        event:PrivateMessageEvent
        private_id = event.user_id
    else:
        sese_matcher.finish()
    
    d_t = threading.Thread(target= download_pics_threading, args=(sese_logger, max_cached_pics_num, 'r18'))
    d_t.start()

    cached_pic = sese_logger.pics_cache_pop('r18')
    logger.success(f'从缓存中获取到图片{cached_pic["meta_data"]["pic_name"]}')

    if needed_msg:= sese_pic_msg_build(cached_pic, pics_noise_path, private_id == 0):
        await send_forward_msg(this_bot, needed_msg, private_id, group_id)

        #消息发送后删除本地文件
        if ori_pic_path := cached_pic.get('path', ''):
            os.remove(ori_pic_path)
            if private_id == 0:
                os.remove(f'{pics_noise_path}/{cached_pic["meta_data"]["real_pic_name"]}.jpg')
        await sese_matcher.finish()

    sese_logger.roll_back_time_id(id)
    await sese_matcher.finish(onebot11_Message([onebot11_MessageSegment.reply(message_id), onebot11_MessageSegment.text('图片获取失败了……')]))



