from pydantic import BaseModel, validator
import os


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
    
    @validator('keyword_answer_lexicon_path')
    def check_lexicon_file(cls, v: str) -> str:
        v = v.replace('\\', '/')
        if not os.path.exists(v):
            r_dirs = '/'.join(v.split('/')[:-1])
            os.makedirs(r_dirs)
            with open(v, 'w', encoding='utf-8') as f:
                f.write('[saki1]\nkeywords = [ "我什么都愿意做",]\nanswers = [ "你这个人，真是满脑子都只想着自己呢。",]')

        return v

