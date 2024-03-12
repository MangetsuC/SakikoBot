import time
import os
import threading
import toml

class Sese_logger:
    def __init__(self, root_path: dict[str, str] = dict(), interval_time: int = 30, proxy = 'i.pixiv.re') -> None:
        self.interval_time = interval_time
        self.proxy = proxy

        self.last_time18 = 0
        self.last_time18_bk = 0
        self.this_time18 = 0

        self.path: dict[str, str] = dict(pixiv = './sesep/pixiv', r18 = './sesep/r18', setu = './sesep/setu', noise = './sesep/noise')
        self.path.update(root_path)

        self.cache_pics: dict[str, list[dict]] = dict(pixiv = list(), r18 = list(), setu = list())

        self.timer = dict()

        self.pop_locks: dict[str, threading.Lock] = dict(pixiv = threading.Lock(), r18 = threading.Lock(), setu = threading.Lock())

    def load_init_cache(self, max_saved_num: int, sort: str = 'pixiv') -> None:
        if os.path.exists(f'{self.path[sort]}/cache.toml'):
            with open(f'{self.path[sort]}/cache.toml', 'r', encoding='utf-8') as f:
                f_txt = f.read()
            if f_txt:
                self.cache_pics[sort].extend(toml.loads(f_txt).get('cache', []))

                if len(self.cache_pics[sort]) > max_saved_num:
                    for i in self.cache_pics[sort][max_saved_num:]:
                        os.remove(i['path'])

                    self.cache_pics[sort] = self.cache_pics[sort][0:max_saved_num]
                return 

        locals = os.listdir(self.path[sort])
        tmp_cnt = 0
        for pic in locals:
            if pic == 'cache.toml':
                continue
            if tmp_cnt < max_saved_num:
                path = f'{self.path[sort]}/{pic}'
                real_name = pic.split('.')[0]
                pid = real_name.split('_')[0]

                self.pics_cache_push(dict(path = path, 
                                        meta_data = dict(pic_name = pic, real_pic_name = real_name, pid = pid, url = '')),
                                        sort)
            else:
                os.remove(f'{self.path[sort]}/{pic}') #删除过多的本地文件
            tmp_cnt += 1
        self.dump_cache(sort)

    def dump_cache(self, sort: str = 'pixiv') -> None:
        '写入缓存文件，注意竞争冒险'
        with open(f'{self.path[sort]}/cache.toml', 'w', encoding='utf-8') as f:
            tmp_list = self.cache_pics[sort]
            f.write(toml.dumps(dict(cache = tmp_list)))

    def update_interval_time(self, interval_time: int) -> None:
        self.interval_time = interval_time

    def check_timer_id(self, id: int) -> int:
        '对对应id检查冷却时间'
        if id not in self.timer:
            self.timer[id] = dict(last_time = 0, last_time_bk = 0, this_time = 0, check_time = 0)

        self.timer[id]['this_time'] = int(time.time())

        tmp_check_time = self.timer[id]['check_time']
        self.timer[id]['check_time'] = self.timer[id]['this_time']

        if self.timer[id]['this_time'] - self.timer[id]['last_time'] < self.interval_time:
            if self.timer[id]['this_time'] - tmp_check_time < 2:
                return -1
            return (self.interval_time - self.timer[id]['this_time'] + self.timer[id]['last_time'])
        
        self.timer[id]['last_time_bk']  = self.timer[id]['last_time']
        self.timer[id]['last_time'] = self.timer[id]['this_time']
        return 0
    
    def roll_back_time_id(self, id: int) -> None:
        '重置对应id冷却时间，用于发送图片失败的情况'
        self.timer[id]['last_time'] = self.timer[id]['last_time_bk']

    def check_timer_18(self) -> int:
        'r18冷却时间，不分id'
        self.this_time18 = int(time.time())

        self.check_time18 = self.this_time18
        if self.this_time18 - self.last_time18 < self.interval_time:
            return (self.interval_time - self.this_time18 + self.last_time18)
        self.last_time18_bk = self.last_time18
        self.last_time18 = self.this_time18
        return 0
    
    def roll_back_time_18(self) -> None:
        self.last_time18 = self.last_time18_bk

    def pics_cache_push(self, data: dict, para_sort: str = 'pixiv') -> None:
        '''存入图片缓存，data的内容应该包含
        path:图片本地路径
        meta_data:dict(
                    pic_name:图片名称
                    real_pic_name:无拓展名图片名称
                    pid:图片pid
                    url:图片地址
                    )
        '''
        self.cache_pics[para_sort].append(data)

    def pics_cache_pop(self, para_sort: str = 'pixiv') -> dict:
        for _ in range(2):
            start_time = time.time()

            tmp = dict()
            if para_sort == 'pixiv':
                self.pop_locks[para_sort].acquire()
                self.pop_locks['setu'].acquire()
                while time.time() - start_time < 10:
                    if len(self.cache_pics[para_sort]) != 0:
                        tmp = self.cache_pics[para_sort].pop()
                    elif len(self.cache_pics['setu']) != 0:
                        tmp = self.cache_pics['setu'].pop()

                    if tmp:
                        self.pop_locks[para_sort].release()
                        self.pop_locks['setu'].release()
                        return tmp
                    time.sleep(0.2)
                
                #self.pop_locks[para_sort].release()
                #self.pop_locks['setu'].release()

            else:
                self.pop_locks[para_sort].acquire()
                while time.time() - start_time < 10:
                    if len(self.cache_pics[para_sort]) != 0:
                        tmp = self.cache_pics[para_sort].pop()
                        
                        self.pop_locks[para_sort].release()
                        return tmp
                    time.sleep(0.2)
                self.pop_locks[para_sort].release()
                break

        return dict(path = '', meta_data = dict())
    
    def get_pics_cache_len(self, para_sort: str = 'pixiv') -> int:
        return len(self.cache_pics[para_sort])
    
      




