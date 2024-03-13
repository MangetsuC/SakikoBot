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

    setu_pixiv_path: str = './sese_pics/pixiv'
    setu_setu_path: str = './sese_pics/setu'
    setu_r18_path: str = './sese_pics/r18'
    setu_noise_path: str = './sese_pics/noise'

    @classmethod
    def create_dirs(cls, path: str) -> bool:
        if not os.path.exists(path):
            os.makedirs(path)
            return True
        return False


    @validator('setu_pic_noise_num')
    def check_noise_num(cls, v: int) -> int:
        if isinstance(v, int):
            if v >= 0:
                return v
        logger.error('Plugin setu pic noise num must be a non-negative integer')
        return 500
    
    @validator('setu_setu_path')
    def check_setu_path(cls, p: str) -> str:
        if cls.create_dirs(p):
            logger.info(f'创建Plugin setu setu类型图片路径：{p}')
        return p
    
    @validator('setu_r18_path')
    def check_r18_path(cls, p: str) -> str:
        if cls.create_dirs(p):
            logger.info(f'创建Plugin setu r18类型图片路径：{p}')
        return p

    @validator('setu_noise_path')
    def check_noise_path(cls, p: str) -> str:
        if cls.create_dirs(p):
            logger.info(f'创建Plugin setu 发送图片前噪点图片存储路径：{p}')
        return p
    
