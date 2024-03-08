from nonebot.log import logger
import toml, feedparser, os, threading

from os import path

from .url_functions import get_new_entries

class Users_subs:
    def __init__(self, root_path: str) -> None:
        self.root_path = root_path
        
        self.users = self.load_users()
        self.subs_data = self.load_subs_data()

        self.private_to_do: list[int] = []
        self.group_to_do: list[int] = []
        self.private_msg_to_do: dict[int, list[dict[str, str | int]]] = dict()
        self.group_msg_to_do: dict[int, list[dict[str, str | int]]] = dict()

        self.lock = threading.Lock()

    def load_users(self) -> dict[list[int], list[int]]:
        '读取用户列表，分私聊与群组消息'
        if not path.exists(f'{self.root_path}/users.toml'):
            f = open(f'{self.root_path}/users.toml', 'w', encoding='utf-8')
            f.close()

        with open(f'{self.root_path}/users.toml', 'r', encoding='utf-8') as f:
            users: dict[list[int], list[int]] = toml.load(f)
            if 'user' not in users:
                users['user'] = list()

            if 'group' not in users:
                users['group'] = list()

        users['user'] = list(set(users['user']))
        users['group'] = list(set(users['group']))

        return users
    
    def reload_users(self) -> None:
        self.users = self.load_users()

    def add_private_user(self, user_id: int) -> None:
        if user_id not in self.users['user']:
            self.users['user'].append(user_id)

    def add_group_user(self, group_id: int) -> None:
        if group_id not in self.users['group']:
            self.users['group'].append(group_id)

    def add_user(self, marked_id: str) -> None:
        '新增用户，不会写入文件，需要调用users_dumps方法'
        if 'private' in marked_id:
            self.add_private_user(int(marked_id.split('_')[-1]))
        elif 'group' in marked_id:
            self.add_group_user(int(marked_id.split('_')[-1]))

    def get_private_user(self) -> list[int]:
        return self.users['user']
    
    def get_group_user(self) -> list[int]:
        return self.users['group']

    def load_subs_data(self) -> dict[str, dict[str, dict[str, str | list]]]:
        '读取订阅数据，依文件读取，返回一个字典'
        tmp = dict()
        for id in self.get_private_user():
            if not path.exists(f'{self.root_path}/{self.to_private_str(id)}.toml'):
                f = open(f'{self.root_path}/{self.to_private_str(id)}.toml', 'w', encoding='utf-8')
                f.close()

            with open(f'{self.root_path}/{self.to_private_str(id)}.toml', 'r', encoding='utf-8') as f:
                tmp[f'{self.to_private_str(id)}'] = toml.load(f)
        
        for id in self.get_group_user():
            if not path.exists(f'{self.root_path}/{self.to_group_str(id)}.toml'):
                f = open(f'{self.root_path}/{self.to_group_str(id)}.toml', 'w', encoding='utf-8')
                f.close()

            with open(f'{self.root_path}/{self.to_group_str(id)}.toml', 'r', encoding='utf-8') as f:
                tmp[f'{self.to_group_str(id)}'] = toml.load(f)

        return tmp
    
    def reload_subs_data(self) -> None:
        self.subs_data = self.load_subs_data()
    
    def users_dumps(self) -> None:
        with open(f'{self.root_path}/users.toml', 'w', encoding='utf-8') as f:
            f.write(toml.dumps(self.users))

    def subs_data_dumps(self, marked_id: str) -> None:
        with open(f'{self.root_path}/{marked_id}.toml', 'w', encoding='utf-8') as f:
            f.write(toml.dumps(self.subs_data.get(marked_id, dict())))

    def subs_data_dumps_all(self) -> None:
        private_list = self.get_private_user()
        group_list = self.get_group_user()

        for i in private_list:
            self.subs_data_dumps(self.to_private_str(i))

        for i in group_list:
            self.subs_data_dumps(self.to_group_str(i))

    def dumps_all(self):
        self.users_dumps()
        self.subs_data_dumps_all()

    def new_sub_entry(self, owner_id: int, marked_id: str, entry_name: str, url: str, must_include: list[str], no_include: list[str], re_match: str = '', at_users: list[int] = []) -> bool:
        '新建词条，不会写入文件，需要调用subs_data_dumps_all方法'
        if marked_id not in self.subs_data:
            self.subs_data[marked_id] = dict()

        if entry_name in self.subs_data[marked_id]:
            return False
        self.subs_data[marked_id][entry_name] = dict(owner_id = owner_id, 
                                                     url = url, must_include = must_include, no_include = no_include, re_match = re_match, reported_entry = list(), at_users = at_users)
        return True

    def add_reported_entry(self, marked_id: str, entry_name: str, entries: list[str]):
        '记录已上报的条目，但不立即写入文件'
        if marked_id in self.subs_data:
            if entry_name in self.subs_data[marked_id]:
                self.subs_data[marked_id][entry_name]['reported_entry'].extend(entries)


    def check_sub_owner(self, id: int, marked_id: str, entry_name: str) -> int:
        if marked_id in self.subs_data:
            if entry_name in self.subs_data[marked_id]:
                owner_id = self.subs_data[marked_id][entry_name]['owner_id']
                if id == owner_id:
                    return 0
                return owner_id
        return -1

    def get_sub_entries_name(self, marked_id: str) -> list[str]:
        '返回对应id的全部订阅名称'
        return list(self.subs_data[marked_id].keys())
    
    def get_sub_entry_data(self, marked_id: str, entry_name: str) -> dict[str, str | list]:
        '返回对应id对应订阅名称的数据'
        return self.subs_data[marked_id][entry_name]
    
    def del_private_user(self, user_id: int):
        '不会写入文件，需要调用users_dumps方法'
        if user_id in self.users['user']:
            self.users['user'].remove(user_id)

    def del_group_user(self, group_id: int):
        '不会写入文件，需要调用users_dumps方法'
        if group_id in self.users['group']:
            self.users['group'].remove(group_id)

    def del_entry(self, marked_id: str, entry_name: str) -> bool:
        '不会写入文件，需要调用subs_data_dumps方法'
        if marked_id in self.subs_data:
            if entry_name in self.subs_data[marked_id]:
                del self.subs_data[marked_id][entry_name]
                return True
        return False

    def del_outdated_file(self) -> None:
        '删除不再存在的用户对应的订阅数据'
        private_list = self.get_private_user()
        group_list = self.get_group_user()

        existed_files = os.listdir(self.root_path)

        for i in existed_files:
            if i != 'users.toml':
                tmp = i.split('.')[0].split('_')
                if tmp[0] == 'private':
                    if int(tmp[1]) not in private_list:
                        os.remove(f'{self.root_path}/{i}')
                else:
                    if int(tmp[1]) not in group_list:
                        os.remove(f'{self.root_path}/{i}')
        self.reload_subs_data()

    def del_nodata_users(self) -> None:
        '删除没有订阅数据的用户，不会立刻写入文件'
        private_list = self.get_private_user()
        group_list = self.get_group_user()

        for i in private_list:
            if not self.subs_data.get(self.to_private_str(i), dict()):
                self.del_private_user(i)

        for i in group_list:
            if not self.subs_data.get(self.to_group_str(i), dict()):
                self.del_group_user(i)

    def add_at_user(self, marked_id: str, entry_name: str, at_users: list[int]) -> bool:
        '添加需要通知的用户'
        is_updated = False
        if marked_id in self.subs_data:
            if entry_name in self.subs_data[marked_id]:
                for u in at_users:
                    if u not in self.subs_data[marked_id][entry_name]['at_users']:
                        is_updated = True
                        self.subs_data[marked_id][entry_name]['at_users'].append(u)
                if is_updated:
                    self.subs_data_dumps(marked_id)
                return True
        return False
    
    def get_at_users(self, marked_id: str, entry_name: str) -> list[int]:
        if marked_id in self.subs_data:
            if entry_name in self.subs_data[marked_id]:
                return self.subs_data[marked_id][entry_name]['at_users']
        return []

    def add_private_todo(self, id: int, new_list: list[dict[str, str | list[str] | list[int]]]):
        '''
        new_list = [{'subs_name': subs_name, 'new_entries': ['entry_name', 'enclosure_link', ...], 'at_users': [qq1, qq2...]}, ...]
        
        '''
        self.private_to_do.append(id)
        self.private_msg_to_do[id] = new_list

    def add_group_todo(self, id: int, new_list: list[dict[str, str | list[str] | list[int]]]):
        self.group_to_do.append(id)
        self.group_msg_to_do[id] = new_list

    def todo_clear(self) -> None:
        self.private_to_do.clear()
        self.private_msg_to_do.clear()
        self.group_to_do.clear()
        self.group_msg_to_do.clear()

    def check_todo_finish(self) -> bool:
        if len(self.private_to_do) == 0 and len(self.group_to_do) == 0:
            return True
        return False
    


    @classmethod
    def to_private_str(cls, id: int) -> str:
        return f'private_{id}'
    
    @classmethod
    def to_group_str(cls, id: int) -> str:
        return f'group_{id}'



def check_to_do(users_subs: Users_subs) -> None:
    if not users_subs.lock.acquire(blocking=False):
        return 

    if not users_subs.check_todo_finish():
        return
    
    logger.info(f'开始检索订阅更新')
    p_users = users_subs.get_private_user()
    g_users = users_subs.get_group_user()

    for p in p_users:
        entries = users_subs.get_sub_entries_name(f'private_{p}') #订阅条目的名称
        todo_list = []
        for e in entries:
            e_data = users_subs.get_sub_entry_data(f'private_{p}', e)
            todo = get_new_entries(e_data['url'], e_data['must_include'], e_data['no_include'], e_data['reported_entry'])
            if todo:
                #数据要进行格式修改
                logger.info(f'用户{p}的订阅{e}有更新，已缓存')
                results_list = []
                for k in todo:
                    results_list.append(k)
                    results_list.append(todo[k])
                todo_list.append(dict(subs_name = e, new_entries = results_list, at_users = []))

        users_subs.add_private_todo(p, todo_list)
    
    for g in g_users:
        entries = users_subs.get_sub_entries_name(f'group_{g}')
        todo_list = []
        for e in entries:
            e_data = users_subs.get_sub_entry_data(f'group_{g}', e)
            todo = get_new_entries(e_data['url'], e_data['must_include'], e_data['no_include'], e_data['reported_entry'])
            if todo:
                logger.info(f'群{g}的订阅{e}有更新，已缓存')
                results_list = []
                for k in todo:
                    results_list.append(k)
                    results_list.append(todo[k])
                todo_list.append(dict(subs_name = e, new_entries = results_list, 
                                      at_users = users_subs.get_at_users(Users_subs.to_group_str(g), e)))

        users_subs.add_group_todo(g, todo_list)
    
    logger.info(f'订阅更新检索完成')
    users_subs.lock.release()
    

