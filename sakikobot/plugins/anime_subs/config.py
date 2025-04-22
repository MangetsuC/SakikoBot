from pydantic import BaseModel, validator


class Config(BaseModel):
    """Plugin Config Here"""

    subs_data_root_path: str = './devconfig/anime_subs'
    check_interval_minutes: int = 10


    @validator('check_interval_minutes')
    def check_noise_num(cls, v: int) -> int:
        if isinstance(v, int):
            if v >= 1:
                return v
        return 10
