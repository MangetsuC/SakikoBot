import feedparser, re
import socket
socket.setdefaulttimeout(5.0)

def get_parser(url: str) -> dict:
    return feedparser.parse(url)

def get_entries_title(parser: dict, must_include: list[str], no_include: list[str], max_num: int = 10) -> list[str]:
    ans: list[str] = []
    if parser.get('status', 404) == 200:
        entries: list[dict[str, str]] = parser.get('entries', [])
        for e in entries:
            e_title = e.get('title', '')
            if check_title(e_title, must_include, no_include):
                ans.append(e_title)
        if len(ans) > max_num:
            return ans[:max_num]
    return ans

def get_new_entries(url: str, must_include: list[str], no_include: list[str], reported_entry: list[str], 
                    r_entry_with_url: list[dict[str, str]] = [], max_num: int = 50) -> dict[str, dict[str, str]]:
    tmp: dict = feedparser.parse(url)
    ans: dict[str, dict[str, str]] = dict()

    e_name_with_url = [x['name'] for x in r_entry_with_url]

    if tmp.get('status', 404) == 200:
        matched_entries: list[dict] = []
        entries: list[dict[str, str]] = tmp.get('entries', [])
        for e in entries:
            e_title = e.get('title', '')
            if check_title(e_title, must_include, no_include):
                matched_entries.append(e)
        if len(matched_entries) > max_num:
            matched_entries = matched_entries[:max_num]

        for e in matched_entries:
            e_title = e.get('title', 'error')
            t_list = e.get('links', [])
            torrent_link = ''
            for i in t_list:
                if 'rel' in i:
                    if i['rel'] == 'enclosure':
                        torrent_link = i.get('href', 'errpr')
                        break
            if e_title not in reported_entry:
                is_reported = False
                is_lack_url = False
            else:
                is_reported = True
                if e_title in e_name_with_url:
                    is_lack_url = False
                else:
                    is_lack_url = True
            
            ans[e.get('title', 'error')] = dict(link = torrent_link, reported = is_reported, lack_url = is_lack_url)
    return ans

def check_title(title: str, must_include: list[str], no_include: list[str]) -> bool:
    is_meet = 0
    for m_str in must_include:
        if m_str not in title:
            break
    else:
        is_meet += 1

    for n_str in no_include:
        if n_str in title:
            break
    else:
        is_meet += 1

    if is_meet >= 2:
        return True
    return False

def get_possible_episode(title: str) -> list[int]:
    t_len = len(title)
    possible_episode = []
    results = re.findall('\d+', title)
    if results:
        for r in results:
            is_check_pre = True
            is_check_aft = True
            if (pos:= title.find(r)) >= 0:
                if pos == 0: #跳过前一字符检测
                    is_check_pre = False
                if pos == t_len - 1: #跳过后一字符检测
                    is_check_aft = False

                if is_check_pre:
                    #if 'a' <= title[pos - 1].lower() <= 'z' or '\u4e00' <= title[pos - 1] <= '\u9fff':
                    if title[pos - 1].isalpha():
                        continue
                if is_check_aft:
                    #if 'a' <= title[pos + 1].lower() <= 'z' or '\u4e00' <= title[pos + 1] <= '\u9fff':
                    if title[pos + 1].isalpha():
                        continue
                
                possible_episode.append(int(r))

    return possible_episode









