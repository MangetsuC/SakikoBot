from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import json
import time

def open_bytes_PIL(img_bytes: bytes) -> Image.Image:
    return Image.open(BytesIO(img_bytes))

def get_colors(this_episode: int, update_episodes: list[int], exist_episodes: list[int]) -> list[tuple]:
    #[(字体颜色), (内部颜色), (边框颜色)]
    
    if this_episode in update_episodes:
        return [(34, 145, 0), (199, 226, 189), (34, 145, 0)]
    elif this_episode in exist_episodes:
        return [(51, 75, 143), (209, 224, 244), (78, 115, 218)]
    else:
        return [(144, 144, 144), (224, 224, 224), (182, 182, 182)]

def draw_squre_poster2(img: Image.Image, episodes: list[int], update_episodes: list[int], exist_episodes: list[int], font_set: dict, font_set_small = None) -> Image.Image:

    episodes.extend(update_episodes)
    episodes.extend(exist_episodes)
    episodes = list(set(episodes))
    episodes.sort()

    tmp_episodes = []
    episode_cut_step = 0
    while len(episodes) + len(tmp_episodes) > 16:
        if len(episodes) > 0:
            if episode_cut_step == 0:
                target_eps = episodes.pop(0)
            else:
                target_eps = episodes.pop(1)

            if target_eps in update_episodes or target_eps in exist_episodes:
                tmp_episodes.append(target_eps)

        episode_cut_step = (episode_cut_step + 1) % 2

        if len(tmp_episodes) > 16:
            tmp_episodes = tmp_episodes[-17:-1]

    episodes.extend(tmp_episodes)
    episodes.sort()

    tmp_width, tmp_height = img.size
    img = img.resize((800, int(tmp_height / tmp_width * 800)))

    tmp_width, tmp_height = img.size

    font_path = font_set.get('path', None)
    font_size = font_set.get('size', 40)

    if font_path == None:
        raise ValueError
    ft = ImageFont.truetype(font_path, size = font_size)
    if font_set_small == None:
        ft_small = ft
    else:
        font_path_small = font_set_small.get('path', None)
        font_size_small = font_set_small.get('size', 40)
        ft_small = ImageFont.truetype(font_path_small, size = font_size_small)

    poster_img = Image.new('RGB', (tmp_width, tmp_height + 200), (255,255,255))
    poster_img.paste(img, (0, 0, tmp_width, tmp_height))

    poster_drawer = ImageDraw.Draw(poster_img)
    
    for j in range(2):
        for i in range(8):
            if episodes != []:
                this_episode = episodes.pop(0)
                txt_color, fill_color, outline_color = get_colors(this_episode, update_episodes, exist_episodes)
                if isinstance(this_episode, int):
                    this_episode_txt = str(this_episode).rjust(2, '0')
                else:
                    this_episode_txt = f'{this_episode:.1f}'
                poster_drawer.rectangle((100*i+10, tmp_height+100*j+10, 100*i+90, tmp_height+100*j+90), fill=fill_color, outline=outline_color, width=2)
                if len(this_episode_txt) > 3:
                    t_ft = ft_small
                else:
                    t_ft = ft
                _, eposide_txt_offset_y, eposide_txt_size_x, eposide_txt_size_y = t_ft.getbbox(this_episode_txt)
                poster_drawer.text((100*i+int(50-eposide_txt_size_x/2), 
                                    tmp_height + 100*j + int(50 - (eposide_txt_size_y - eposide_txt_offset_y)/2 - eposide_txt_offset_y)), 
                                    this_episode_txt, font = t_ft, fill = txt_color)
            else:
                break

    return poster_img


def img_save(img: Image.Image, path) -> None:
    img.convert('RGB').save(path, 'PNG')

def img_to_BytesIO(img: Image.Image) -> BytesIO:
    tmp_io = BytesIO()
    # img.convert('RGB').save(tmp_io, format='PNG')
    img.convert('RGB').save(tmp_io, format='JPEG', quality = 100)
    return tmp_io




if __name__ == '__main__':
    #'./devconfig/consola.ttf'
    # with open('./devconfig/anime_subs/images/509986.jpg', 'rb') as f:
    #    img_bytes = f.read()
    # img = open_bytes_PIL(img_bytes)

    #subject_id = 506922
    subject_id = 403238

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}
    
    # r = requests.get(f'https://api.bgm.tv/v0/episodes?subject_id={subject_id}&limit=100&offset=0', headers = headers)
    # if r.status_code == 200:
    #     tmp_eps = []
    #     data: dict = json.loads(r.text)['data']
    #     for e in data:
    #         if e['type'] == 0:
    #             tmp_eps.append(e['sort'])

    #     print(tmp_eps)



    #生成框框图片，基本完成
    # r = requests.get(f'https://api.bgm.tv/v0/subjects/{subject_id}', headers = headers)
    # if r.status_code == 200:
    #     data = json.loads(r.text)
    #     img_url = data['images']['large']
    #     r_img = requests.get(img_url, headers = headers)
    #     if r_img.status_code == 200:
    #         img_bytes = r_img.content
    #         img = open_bytes_PIL(img_bytes)
    #         font_set = {'path': './devconfig/consola.ttf', 'size': 40}
    #         font_set_s = {'path': './devconfig/consola.ttf', 'size': 32}
    #         tmp_img = draw_squre_poster2(img, [1,2,3,4,5,6,7,8,9,10,11,12,13,14.5], [4], [2, 3], font_set, font_set_s)
    #         img_save(tmp_img, './devconfig/anime_subs/images/509986_poster.jpg')


    current_date = time.strftime('%Y-%m-%d')
    current_date_list = current_date.split('-')
    current_date_list[0] = str(int(current_date_list[0]) - 1)
    start_date = '-'.join(current_date_list)


    keyword = '败犬女主太多了'
    keywords = keyword.split(' ')
    api_keyword = ' '.join([f'"{x}"' for x in keywords])
    dict_data = dict(keyword = api_keyword, filter = dict(type = [2], air_date = [f'>={start_date}', f'<={current_date}']))
    # dict_data = dict(keyword = api_keyword)
    r = requests.post(f'https://api.bgm.tv/v0/search/subjects', headers = headers, 
                        json=dict_data)
    if r.status_code == 200:
        t_subject_id = json.loads(r.text)['data'][0]['id']
        print(t_subject_id)
    

    #https://api.bgm.tv/v0/episodes?subject_id=403238&limit=100&offset=0

    
    pass

