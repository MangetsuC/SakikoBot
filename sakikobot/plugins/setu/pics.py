import os, requests, cv2, random

from .sese import Sese_logger

def pic_resize_max(pic: cv2.typing.MatLike, target_max_size: int) -> cv2.typing.MatLike:
    tmp_height, tmp_width, _ = pic.shape
    if (max_one_size:= max(tmp_height, tmp_width)) > target_max_size:
        tmp_height = int(target_max_size/max_one_size*tmp_height)
        tmp_width = int(target_max_size/max_one_size*tmp_width)
    
    return cv2.resize(pic, (tmp_width, tmp_height))

def pic_compress_save(pic: cv2.typing.MatLike, path: str, quality: int = 95) -> None:
    if path.split('.')[-1] != 'jpg':
        raise ValueError('Compressed picture must be jpg file...')
    
    cv2.imwrite(path, pic, [int(cv2.IMWRITE_JPEG_QUALITY), quality])

def pic_noise(pic: cv2.typing.MatLike, noise_num: int) -> cv2.typing.MatLike:
    tmp_height, tmp_width, _ = pic.shape
    for _ in range(noise_num):
        cv2.circle(pic, (random.randint(1, tmp_height - 1), random.randint(1, tmp_width - 1)), 1, (255, 255, 255), -1, 2)
    return pic

def download_pics_threading(base_path: str, noise_path: str, logger: Sese_logger, max_local_pics_num: int, max_cached_pics_num: int, para_sort = 'pixiv') -> None:
    for _ in range(5):
        saved_pics = os.listdir(base_path)
        saved_pics.sort(key = lambda x: os.path.getmtime(f'{base_path}/{x}'), reverse=True) #按时间删除，避免记录的图片路径的本地文件被删除
        while len(saved_pics) > max_local_pics_num:
            os.remove(f'{base_path}/{saved_pics.pop()}') #要对文件夹做剔除

        saved_pics = os.listdir(noise_path)
        while len(saved_pics) > max_local_pics_num:
            os.remove(f'{noise_path}/{saved_pics.pop()}') #要对文件夹做剔除

        if logger.get_pics_cache_len(para_sort) >= max_cached_pics_num: #记录的图片路径数量不得超过本地图片数量，避免本地图片被删除
            break

        r = requests.post('https://moe.jitsu.top/api', params=dict(sort = para_sort, type = 'json', num = 1))
        if r.status_code == 200:
            r.encoding = 'utf-8'
            pic_ori_url: str = r.json()['pics'][0]
            pic_name = pic_ori_url.split('/')[-1]
            pic_data = pic_name.split('.')
            real_pic_name = pic_data[0]
            if len(pic_data) == 2:
                pic_data[0] = pic_data[0].split('_')
            pic_pid = pic_data[0][0]

            pic = requests.get(url=pic_ori_url)
            if pic.status_code == 200:
                full_path = f'{base_path}/{pic_name}'
                f = open(full_path, 'wb')
                f.write(pic.content)
                f.close()
                logger.pics_cache_push(dict(path = full_path, meta_data = dict(pic_name = pic_name, real_pic_name = real_pic_name, pid = pic_pid)), para_sort)
                break







