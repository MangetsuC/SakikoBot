from pydantic import BaseModel, validator


class Config(BaseModel):
    """Plugin Config Here"""

    subs_data_root_path: str = './devconfig/anime_subs'
    check_interval_minutes: int = 10
    font_normal_path: str = './devconfig/consola.ttf'
    font_normal_size: int = 40
    font_small_path: str = './devconfig/consola.ttf'
    font_small_size: int = 32


    @validator('check_interval_minutes')
    def check_noise_num(cls, v: int) -> int:
        if isinstance(v, int):
            if v >= 1:
                return v
        return 10
