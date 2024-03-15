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

def img_stack_v(imgs: list[Image.Image|str], margin_line: int = 5, margin_border: tuple[int] = (10, 10, 10, 10), align: str = 'center') -> Image.Image:
    '''
    margin_border: tuple(left, right, top, bottom)
    '''
    img_x = 0
    img_y = 0

    for i in imgs:
        if isinstance(i, Image.Image):
            tmp_size = i.size
            if tmp_size[0] > img_x:
                img_x = tmp_size[0]

            img_y += (tmp_size[1] + margin_line)
        elif i == 'line':
            img_y += (4 + margin_line)
        elif i == 'space':
            img_y += (20 + margin_line)
        else:
            continue

    img_y -= margin_line

    a_img = Image.new('RGB', [img_x + margin_border[0] + margin_border[1], img_y + margin_border[2] + margin_border[3]], 0xffffff)
    y_shift = 0
    for i in range(len(imgs)):
        tmp_img = imgs[i]
        if isinstance(tmp_img, str):
            #特殊字符处理
            tmp_len = len(tmp_img)
            if tmp_len >= 4 and tmp_img[0:4] == 'line':
                line_para = tmp_img.split(' ')
                if len(line_para) > 1:
                    line_h = int(line_para[1])
                else:
                    line_h = 4
                tmp_img = Image.new('RGB', [img_x, line_h], 0xd0d7de)
            elif tmp_img == 'space':
                y_shift += (8 + margin_line)
                continue
            else:
                continue

        i_size = tmp_img.size

        if align == 'center':
            pos_x = int((img_x - i_size[0]) / 2 + margin_border[0])
        elif align == 'left':
            pos_x = margin_border[0]
        elif align == 'right':
            pos_x = img_x + margin_border[0] - i_size[0]
        else:
            raise ValueError(f'No alignment {align} in img_stack_v')
        pos_y = margin_border[2] + y_shift
        y_shift += (i_size[1] + margin_line)
        a_img.paste(tmp_img, (pos_x, pos_y))

    return a_img

def img_stack_h(imgs: list[Image.Image|str], margin_line: int = 5, margin_border: tuple[int] = (10, 10, 10, 10), align: str = 'center') -> Image.Image:
    new_imgs = []
    for i in range(len(imgs)-1, -1, -1):
        if isinstance(imgs[i], Image.Image):
            new_imgs.append(imgs[i].rotate(90, expand=True))
        else:
            new_imgs.append(imgs[i])

    if align == 'center':
        v_align = 'center'
    elif align == 'top':
        v_align = 'left'
    elif align == 'bottom':
        v_align = 'right'
    else:
        raise ValueError(f'No alignment {align} in img_stack_h')

    return img_stack_v(new_imgs, margin_line, margin_border, v_align).rotate(-90, expand=True)

def img_to_BytesIO(img: Image.Image) -> io.BytesIO:
    tmp_io = io.BytesIO()
    img.save(tmp_io, format='JPEG')
    return tmp_io










