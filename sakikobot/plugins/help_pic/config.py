from pydantic import BaseModel, validator
import requests
import os

from nonebot.log import logger


class Config(BaseModel):
    """Plugin Config Here"""

    help_font_path: str = './SourceHanSansSC.otf'
    help_large_font_size: int = 50
    help_medium_font_size: int = 35
    help_small_font_size: int = 25

    def check_font(self) -> None:
        tmp_dir = '/'.join(self.help_font_path.split('/')[:-1])
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        if not os.path.exists(self.help_font_path):
            #下载部分还没有完成
            return 
            try:
                logger.info('正在下载字体文件……')
                font_r = requests.get(url='https://github.com/adobe-fonts/source-han-sans/raw/release/Variable/OTF/SourceHanSansSC-VF.otf', 
                                      #https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansCN.zip
                              timeout=(2, 3))
                if font_r.status_code == 200:
                    with open(self.help_font_path, 'wb') as f:
                        f.write(font_r.content)
                    logger.info('字体文件下载完成！')
                    return 
            except BaseException:#requests.exceptions.Timeout or requests.exceptions.ConnectionError:
                pass

            logger.error('字体文件下载失败，请检查您的网络连接，本插件将被禁用！')
        return 

    @validator('help_font_path')
    def check_font_path(cls, v: str) -> str:
        return v.replace('\\', '/')

