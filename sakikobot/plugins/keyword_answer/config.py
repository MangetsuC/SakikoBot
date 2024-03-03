from pydantic import BaseModel, validator


class Config(BaseModel):
    """Plugin Config Here"""

    keyword_answer_lexicon_path: str = './sakikobot/plugins/keyword_answer/keyword_answer_lexicon.toml'
    keyword_answer_answer_priority: int = 10
    keyword_answer_command_priority: int = 4
    keyword_answer_enable: bool = True

    @validator('keyword_answer_answer_priority')
    def check_priority_answer(cls, v: int) -> int:
        if v >= 1:
            return v
        raise ValueError('plugin keyword_answer priority must greater than 1')
    
    @validator('keyword_answer_command_priority')
    def check_priority_command(cls, v: int) -> int:
        if v >= 1:
            return v
        raise ValueError('plugin keyword_answer priority must greater than 1')

