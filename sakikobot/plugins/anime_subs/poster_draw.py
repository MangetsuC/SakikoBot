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

    
    pass

