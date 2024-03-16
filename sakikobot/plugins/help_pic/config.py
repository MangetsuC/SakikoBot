from pydantic import BaseModel, validator
import requests
import os

from nonebot.log import logger


class Config(BaseModel):
    """Plugin Config Here"""

    help_font_path: str = 'simhei'
    help_large_font_size: int = 50
    help_medium_font_size: int = 35
    help_small_font_size: int = 25

    @validator('help_font_path')
    def check_font_path(cls, v: str) -> str:
        return v.replace('\\', '/')

