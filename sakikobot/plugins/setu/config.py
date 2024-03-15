from pydantic import BaseModel, validator
from nonebot.log import logger
import os


class Config(BaseModel):
    """Plugin Config Here"""

    setu_proxy: str = 'i.pixiv.re'
    setu_pic_noise_num: int = 200
    setu_interval_time: int = 30
    setu_max_local_pics_num: int = 10
    setu_get_skip_cached_pics_num: int = 6

    setu_max_send_pic_size_kb: int = 500
    setu_max_send_pic_size_pixel: int = 1920
    setu_enable_compressed: bool = True
    setu_enable_noise: bool = True

    setu_pixiv_path: str = './sese_pics/pixiv'
    setu_setu_path: str = './sese_pics/setu'
    setu_r18_path: str = './sese_pics/r18'
    setu_noise_path: str = './sese_pics/noise'

    def create_dirs(self, path: str) -> bool:
        if not os.path.exists(path):
            os.makedirs(path)
            return True
        return False
    
    def check_path_exist(self) -> None:
        if self.create_dirs(self.setu_setu_path):
            logger.info(f'创建Plugin setu setu类型图片路径：{self.setu_setu_path}')

        if self.create_dirs(self.setu_pixiv_path):
            logger.info(f'创建Plugin setu pixiv类型图片路径：{self.setu_pixiv_path}')

        if self.create_dirs(self.setu_r18_path):
            logger.info(f'创建Plugin setu r18类型图片路径：{self.setu_r18_path}')

        if self.create_dirs(self.setu_noise_path):
            logger.info(f'创建Plugin setu 发送图片前噪点图片存储路径：{self.setu_noise_path}')


    @validator('setu_pic_noise_num')
    def check_noise_num(cls, v: int) -> int:
        if isinstance(v, int):
            if v >= 0:
                return v
        logger.error('Plugin setu pic noise num must be a non-negative integer')
        return 500
    
    @validator('setu_max_send_pic_size_kb')
    def check_max_size_kb(cls, v: str) -> int:
        v = v.lower()
        try:
            if 'k' in v:
                return int(v.split('k')[0])
            elif 'm' in v:
                return int(v.split('m')[0]) * 1024
            elif 'g' in v:
                return int(v.split('g')[0]) * 1024 * 1024
            else:
                return int(v)
        except BaseException:
            logger.error('Plugin setu pic max size (not pixel) must be a combination of integer and kb or mb or gb')
        return 500
    
    
