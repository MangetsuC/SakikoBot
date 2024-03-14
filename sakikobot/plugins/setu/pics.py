import requests, random
from nonebot.log import logger as nonebot_logger
import urllib3
from PIL import Image, ImageDraw

from .sese import Sese_logger

urllib3.disable_warnings()

def pic_resize_max_PIL(pic: Image.Image, target_max_size: int) -> Image.Image:
    tmp_width, tmp_height = pic.size
    if (max_one_size:= max(tmp_height, tmp_width)) > target_max_size:
        tmp_height = int(target_max_size/max_one_size*tmp_height)
        tmp_width = int(target_max_size/max_one_size*tmp_width)
    
    return pic.resize((tmp_width, tmp_height))

def pic_compress_save_PIL(pic: Image.Image, path: str, quality: int = 95) -> None:
    if path.split('.')[-1] != 'jpg':
        raise ValueError('Compressed picture must be jpg file...')
    
    pic.convert('RGB').save(path, 'JPEG', quality = quality)

def pic_noise_PIL(pic: Image.Image, noise_num: int) -> None:
    d = ImageDraw.Draw(pic)
    tmp_width, tmp_height = pic.size
    for _ in range(noise_num):
        d.point((random.randint(1, tmp_height - 1), random.randint(1, tmp_width - 1)), fill=(255,255,255))

def download_pics_threading(logger: Sese_logger, max_cached_pics_num: int, para_sort = 'pixiv') -> None:
    for cnt in range(5):
        if len(logger.cache_pics[para_sort]) > max_cached_pics_num:
            #如果已经存储了足够的图片，则跳过
            break

        r = requests.post('https://moe.jitsu.top/api', params=dict(sort = para_sort, type = 'json', num = 1))
        if r.status_code == 200:
            r.encoding = 'utf-8'
            pic_ori_url: str = r.json()['pics'][0]
            pic_name = pic_ori_url.split('/')[-1]
            pic_data = pic_name.split('.')
            real_pic_name = pic_data[0]
            if len(pic_data) == 2 and '_' in pic_data[0]:
                pic_data[0] = pic_data[0].split('_')
                pic_pid = pic_data[0][0]
            else:
                pic_pid = ''

            if pic_pid:
                pic_ori_url = pic_ori_url.replace('i.pixiv.re', logger.proxy)

            try:
                pic = requests.get(url=pic_ori_url, timeout=(2, 3))
            except requests.exceptions.Timeout:
                nonebot_logger.error(f'访问代理服务器超时或是图片已经消失了!尝试次数：{cnt+1}')
                if cnt > 0:
                    para_sort = 'setu'
                continue
            except requests.exceptions.SSLError:
                try:
                    pic = requests.get(url=pic_ori_url, timeout=(2, 3), verify=False)
                except requests.exceptions.Timeout:
                    nonebot_logger.error(f'访问代理服务器超时或是图片已经消失了!尝试次数：{cnt+1}')
                    if cnt > 0:
                        para_sort = 'setu'
                    continue

            if pic.status_code == 200:
                full_path = f'{logger.path[para_sort]}/{pic_name}'
                f = open(full_path, 'wb')
                f.write(pic.content)
                f.close()
                logger.pop_locks[para_sort].acquire()
                logger.pics_cache_push(dict(path = full_path, meta_data = dict(pic_name = pic_name, real_pic_name = real_pic_name, pid = pic_pid, url = pic_ori_url)), para_sort)
                logger.dump_cache(para_sort)
                logger.pop_locks[para_sort].release()
                break
        else:
            nonebot_logger.error(f'从图库api获取图片失败!尝试次数：{cnt+1}')








