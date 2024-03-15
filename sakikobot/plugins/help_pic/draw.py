import PIL, io, math
from PIL import Image, ImageDraw, ImageFont

def load_font(font_path: str) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(font_path)

def set_font_size(ft: ImageFont.FreeTypeFont, f_size: int) -> ImageFont.FreeTypeFont:
    return ft.font_variant(size=f_size)

def txt_draw(txt: str, ft: ImageFont.FreeTypeFont, max_x: int = 1000, f_weight: str = 'thin', color: tuple[int] = (0, 0, 0)) -> Image.Image:
    '实际上字重f_weight是通过描边完成的，除去thin都可能有显示问题，更推荐通过字体来调整字重'
    wrap_char_num = len(txt)
    while (size := ft.getbbox(txt[0:wrap_char_num]))[2] > max_x:
        if wrap_char_num > 2:
            wrap_char_num -= 2
        else:
            raise ValueError(f'最大宽度{max_x}设定太小！')

    r_num = math.ceil(len(txt)/wrap_char_num)
    tmp_img = Image.new('RGB', [size[2], size[3] * r_num], 0xffffff)
    tmp_draw = ImageDraw.Draw(tmp_img)

    if f_weight == 'thin':
        s_width = 0
    elif f_weight == 'normal':
        s_width = 1
    elif f_weight == 'medium':
        s_width = 2
    elif f_weight == 'bold':
        s_width = 3
    else:
        s_width = 0

    for i in range(r_num):
        if (i+1) * wrap_char_num > len(txt):
            tmp_draw.text((0, i * size[3]), txt[i * wrap_char_num:], fill=color, font=ft, stroke_width=s_width, stroke_fill=color)
        else:
            tmp_draw.text((0, i * size[3]), txt[i * wrap_char_num: (i+1) * wrap_char_num], fill=color, font=ft, stroke_width=s_width, stroke_fill=color)

    return tmp_img

def img_stack(imgs: list[Image.Image], margin_line: int = 5, margin_border: tuple[int] = (10, 10, 10, 10)) -> Image.Image:
    '''
    margin_border: tuple(left, right, top, bottom)
    '''
    img_x = 0
    img_y = 0

    for i in imgs:
        tmp_size = i.size
        if tmp_size[0] > img_x:
            img_x = tmp_size[0]

        img_y += (tmp_size[1] + margin_line)

    img_y -= margin_line

    a_img = Image.new('RGB', [img_x + margin_border[0] + margin_border[1], img_y + margin_border[2] + margin_border[3]], 0xffffff)
    y_shift = 0
    for i in range(len(imgs)):
        i_size = imgs[i].size
        pos_x = int((img_x - i_size[0]) / 2 + margin_border[0])
        pos_y = margin_border[2] + y_shift
        y_shift += (i_size[1] + margin_line)
        a_img.paste(imgs[i], (pos_x, pos_y))

    return a_img

def img_to_BytesIO(img: Image.Image) -> io.BytesIO:
    tmp_io = io.BytesIO()
    img.save(tmp_io, format='JPEG')
    return tmp_io










