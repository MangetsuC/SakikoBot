import time

class Sese_logger:
    def __init__(self, interval_time: int = 30) -> None:
        self.interval_time = interval_time

        self.last_time18 = 0
        self.last_time18_bk = 0
        self.this_time18 = 0

        self.cache_pics: dict[str, list[str]] = dict(pixiv = list(), r18 = list())

        self.timer = dict()

    def updata_interval_time(self, interval_time: int) -> None:
        self.interval_time = interval_time

    def check_timer_id(self, id: int) -> int:
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
        self.timer[id]['last_time'] = self.timer[id]['last_time_bk']

    def check_timer_18(self) -> int:
        self.this_time18 = int(time.time())

        self.check_time18 = self.this_time18
        if self.this_time18 - self.last_time18 < self.interval_time:
            return (self.interval_time - self.this_time18 + self.last_time18)
        self.last_time18_bk = self.last_time18
        self.last_time18 = self.this_time18
        return 0
    
    def roll_back_time_18(self) -> None:
        self.last_time18 = self.last_time18_bk

    def pics_cache_push(self, path: str, para_sort: str = 'pixiv') -> None:
        self.cache_pics[para_sort].append(path)

    def pics_cache_pop(self, para_sort: str = 'pixiv') -> dict:
        start_time = time.time()
        while time.time() - start_time < 10:
            if len(self.cache_pics[para_sort]) != 0:
                return self.cache_pics[para_sort].pop()
            time.sleep(0.2)
        return dict(path = '', meta_data = dict())
    
    def get_pics_cache_len(self, para_sort: str = 'pixiv') -> int:
        return len(self.cache_pics[para_sort])
    




