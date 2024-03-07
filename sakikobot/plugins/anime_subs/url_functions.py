import feedparser

def get_entries_title(url: str, must_include: list[str], no_include: list[str], max_num: int = 10) -> list[str]:
    tmp: dict = feedparser.parse(url)
    ans: list[str] = []
    if tmp.get('status', 404) == 200:
        entries: list[dict[str, str]] = tmp.get('entries', [])
        for e in entries:
            e_title = e.get('title', '')
            if check_title(e_title, must_include, no_include):
                ans.append(e_title)
        if len(ans) > max_num:
            return ans[:max_num]
    return ans

def get_new_entries(url: str, must_include: list[str], no_include: list[str], reported_entry: list[str], max_num: int = 10) -> dict[str, str]:
    tmp: dict = feedparser.parse(url)
    ans: dict[str, str] = dict()
    if tmp.get('status', 404) == 200:
        matched_entries: list[dict] = []
        entries: list[dict[str, str]] = tmp.get('entries', [])
        for e in entries:
            e_title = e.get('title', '')
            if check_title(e_title, must_include, no_include):
                if e_title not in reported_entry:
                    matched_entries.append(e)
        if len(matched_entries) > max_num:
            matched_entries = matched_entries[:max_num]

        for e in matched_entries:
            t_list = e.get('links', [])
            torrent_link = ''
            for i in t_list:
                if 'rel' in i:
                    if i['rel'] == 'enclosure':
                        torrent_link = i.get('href', 'errpr')
                        break
            ans[e.get('title', 'error')] = torrent_link
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











