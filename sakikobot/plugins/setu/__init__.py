from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from nonebot import on_keyword, CommandGroup
from nonebot.log import logger
from nonebot.adapters import Event

from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment as onebot11_MessageSegment, Message as onebot11_Message

import threading, os

from .config import Config
from .pics import download_pics_threading, open_PIL, pic_resize_max_PIL, pic_compress_save_PIL, pic_noise_PIL
from .sese import Sese_logger



__plugin_meta__ = PluginMetadata(
    name="setu",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
config.check_path_exist()

max_local_pics_num = config.setu_max_local_pics_num
skip_cached_pics_num = min(config.setu_get_skip_cached_pics_num, max_local_pics_num)

sese_logger = Sese_logger(root_path= dict(pixiv = config.setu_pixiv_path, r18 = config.setu_r18_path, setu = config.setu_setu_path, noise = config.setu_noise_path), 
                          interval_time= config.setu_interval_time,
                          proxy=config.setu_proxy)
sese_logger.load_init_cache(max_local_pics_num)
sese_logger.load_init_cache(max_local_pics_num, 'r18')
sese_logger.load_init_cache(max_local_pics_num, 'setu')

#清空噪点图片
for i in os.listdir(sese_logger.path['noise']):
    os.remove(f'{sese_logger.path["noise"]}/{i}')

t_1 = threading.Thread(target= download_pics_threading, args=(sese_logger, skip_cached_pics_num))
t_r18 = threading.Thread(target= download_pics_threading, args=(sese_logger, skip_cached_pics_num, 'r18'))
t_1.setDaemon(True)
t_r18.setDaemon(True)
t_1.start()
t_r18.start()


def sese_pic_msg_build(cached_pic_data: dict, noise_path: str) -> list[list[onebot11_MessageSegment], str]:
    if pic_path := cached_pic_data.get('path', ''):
        pic_name = cached_pic_data['meta_data']['pic_name']
        real_pic_name = cached_pic_data['meta_data']['real_pic_name']
        pic_pid = cached_pic_data['meta_data'].get('pid', '')
        pic_url = cached_pic_data['meta_data'].get('url', '')

        tmp: list[onebot11_MessageSegment] = []
        if pic_pid:
            tmp.append(onebot11_MessageSegment.text(f'很可能是Pixiv ID:{pic_pid}\n'))

        target_path = pic_path

        tmp_pic = open_PIL(pic_path)
        if config.setu_enable_compressed: #图片压缩处理
            target_path = f'{noise_path}/{real_pic_name}.jpg'
            pic_size = os.path.getsize(pic_path)
            start_max_size = config.setu_max_send_pic_size_pixel
            start_quality = 100
            while pic_size > config.setu_max_send_pic_size_kb * 1024:
                tmp_pic = pic_resize_max_PIL(tmp_pic, start_max_size)
                pic_compress_save_PIL(tmp_pic, target_path, quality=start_quality)

                if start_max_size > 1280:
                    start_max_size = int(start_max_size*0.874)
                elif start_quality > 50:
                    start_quality -= 5

                pic_size = os.path.getsize(target_path)

        if config.setu_enable_noise: #图片增加噪点处理
            pic_noise_PIL(tmp_pic, config.setu_pic_noise_num)
            if config.setu_enable_compressed:
                target_path = f'{noise_path}/{real_pic_name}.jpg'
                pic_compress_save_PIL(tmp_pic, target_path, start_quality + 5 if start_quality < 100 else start_quality)
            else:
                target_path = f'{noise_path}/{pic_name}'
                tmp_pic.save(target_path)

        with open (target_path, 'rb') as file:
            pic_bytes = file.read()
        tmp.append(onebot11_MessageSegment.image(pic_bytes))

        if pic_url:
            tmp.append(onebot11_MessageSegment.text(f'图片源地址:{pic_url}'))

        return [tmp, target_path]
    return [[], '']

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

    d_t = threading.Thread(target= download_pics_threading, args=(sese_logger, skip_cached_pics_num))
    d_t.start()

    cached_pic = sese_logger.pics_cache_pop()
    if cached_pic["meta_data"]:
        logger.success(f'从缓存中获取到图片{cached_pic["meta_data"]["pic_name"]}')
    else:
        logger.warning('未能从缓存中获取到图片')

    needed_msg = sese_pic_msg_build(cached_pic, sese_logger.path['noise'])
    if needed_msg[0]:
        await sese_matcher.send(needed_msg[0])

        #消息发送后删除本地文件
        if ori_pic_path := cached_pic.get('path', ''):
            os.remove(ori_pic_path)
            if os.path.exists(needed_msg[1]): #只有图片需要压缩或增加噪点后才会返回另外的文件地址
                os.remove(needed_msg[1])

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
    message_id = event.message_id
    
    d_t = threading.Thread(target= download_pics_threading, args=(sese_logger, skip_cached_pics_num, 'r18'))
    d_t.start()

    cached_pic = sese_logger.pics_cache_pop('r18')
    logger.success(f'从缓存中获取到图片{cached_pic["meta_data"]["pic_name"]}')

    needed_msg = sese_pic_msg_build(cached_pic, sese_logger.path['noise'])
    if needed_msg[0]:
        await sese_matcher.send(needed_msg[0])

        #消息发送后删除本地文件
        if ori_pic_path := cached_pic.get('path', ''):
            os.remove(ori_pic_path)
            if os.path.exists(needed_msg[1]): #只有图片需要压缩或增加噪点后才会返回另外的文件地址
                os.remove(needed_msg[1])
        await sese_matcher.finish()

    sese_logger.roll_back_time_id(id)
    await sese_matcher.finish(onebot11_Message([onebot11_MessageSegment.reply(message_id), onebot11_MessageSegment.text('图片获取失败了……')]))



