from typing import Annotated, Any

import toml

class Lexicon:
    def __init__(self, lexicon_path) -> None:
        self.path = lexicon_path
        
        self.lexicon = self.load_keyword_answer_lexicon()
        self.matcher_dict, self.matcher_keywords = self.decode_keyword_answer_lexicon()

    def __len__(self) -> int:
        return len(self.lexicon)

    def reload(self) -> None:
        self.matcher_dict, self.matcher_keywords = self.decode_keyword_answer_lexicon()

    def get_keywords(self) -> tuple:
        return tuple(set(self.matcher_keywords))
    
    def get_dict(self) -> dict:
        return self.matcher_dict
    
    def get_candidate(self, keyword) -> str:
        return self.matcher_dict.get(keyword, [])

    def load_keyword_answer_lexicon(self) -> dict:
        '词库读取'
        with open(self.path, 'r', encoding='utf-8') as f:
            ori_lexicon = toml.load(f)

        return ori_lexicon
    
    def decode_keyword_answer_lexicon(self) -> list[dict, list]:
        '词库解析'
        keys_ori_lexicon = self.lexicon.keys()
        matcher_dict = dict()
        matcher_keywords = list() #用于注册事件响应器
        for key in keys_ori_lexicon:
            inner_dict: dict|Any = self.lexicon.get(key, None)
            if isinstance(inner_dict, dict):
                inner_keywords: list|Any = inner_dict.get('keywords', None)
                inner_answers: list|Any = inner_dict.get('answers', None)
                if isinstance(inner_keywords, list) and isinstance(inner_answers, list):
                    for key1 in inner_keywords:
                        key_str = str(key1)
                        matcher_keywords.append(key_str)
                        matcher_dict[key_str] = inner_answers
        return [matcher_dict, matcher_keywords]

    def new_keyword_answer_group(self, group_name:str, keywords:list, answers:list) -> dict:
        tmp = dict(keywords = keywords, answers = answers)
        self.lexicon[group_name] = tmp
        return tmp


    def dumps_keyword_answer_lexicon(self) -> None:
        '词库写入'
        with open(self.path, 'w', encoding='utf-8') as f:
            lexicon_txt = toml.dumps(self.lexicon)
            f.write(lexicon_txt)

    def delete_candidate(self, key: str) -> bool:
        '词条删除'
        if self.lexicon.pop(key, None) is None:
            return False
        return True
    
    def candidate_str(self, key_name: str) -> str:
        if key_name in self.lexicon:
            return f'词条:{key_name}\n关键词:{self.lexicon[key_name]["keywords"]}\n回复词:{self.lexicon[key_name]["answers"]}'
        else:
            return f'词条:{key_name}不存在'

    def candidate_print(self, start_no: int, end_no: int) -> list[int, list[str]]:
        if start_no > len(self.lexicon):
            start_no = len(self.lexicon)
        if end_no > len(self.lexicon):
            end_no = len(self.lexicon)

        ans_list = []
        if (start_no - 1) < 0:
            return [0, []]

        ori_keys_list = list(self.lexicon.keys())
        for i in range(start_no - 1, end_no):
            this_key: str = ori_keys_list[i]
            ans_list.append(self.candidate_str(this_key))

        return [(end_no - start_no + 1), ans_list]







