from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    setu_proxy: str = 'i.pixiv.re'
