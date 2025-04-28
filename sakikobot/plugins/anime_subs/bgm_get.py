import requests
import time
import json

def get_episodes(subject_id: int, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}) -> list[int]|None:
    r = requests.get(f'https://api.bgm.tv/v0/episodes?subject_id={subject_id}&limit=100&offset=0', headers = headers)
    if r.status_code == 200:
        tmp_eps = []
        data: dict = json.loads(r.text)['data']
        for e in data:
            if e['type'] == 0:
                tmp_eps.append(e['sort'])

        return tmp_eps
    return None


def get_image(subject_id: int, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}) -> bytes:
    r = requests.get(f'https://api.bgm.tv/v0/subjects/{subject_id}', headers = headers)
    if r.status_code == 200:
        data = json.loads(r.text)
        img_url = data['images']['large']
        r_img = requests.get(img_url, headers = headers)
        if r_img.status_code == 200:
            img_bytes = r_img.content
            return img_bytes
    return None


def get_subject_id_from_keyword(keyword: str, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}) -> int|None:
    current_date = time.strftime('%Y-%m-%d')
    current_date_list = current_date.split('-')
    current_date_list[0] = str(int(current_date_list[0]) - 1)
    start_date = '-'.join(current_date_list)

    keywords = keyword.split(' ')
    api_keyword = ' '.join([f'"{x}"' for x in keywords])
    dict_data = dict(keyword = api_keyword, filter = dict(type = [2], air_date = [f'>={start_date}', f'<={current_date}']))
    r = requests.post(f'https://api.bgm.tv/v0/search/subjects', headers = headers, 
                        json=dict_data)
    if r.status_code == 200:
        t_subject_id = json.loads(r.text)['data'][0]['id']
        return int(t_subject_id)

    return None















