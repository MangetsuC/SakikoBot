import PIL, io, math
from PIL import Image, ImageDraw, ImageFont

def load_font(font_path: str) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(font_path)

def set_font_size(ft: ImageFont.FreeTypeFont, f_size: int) -> ImageFont.FreeTypeFont:
    return ft.font_variant(size=f_size)

def txt_draw(txt: str, ft: ImageFont.FreeTypeFont, max_x: int = 1000, f_weight: str = 'thin',
              color: tuple[int]|int = 0x000000, bg_color: tuple[int]|int = 0xffffff) -> Image.Image:
    '实际上字重f_weight是通过描边完成的，除去thin都可能有显示问题，更推荐通过字体来调整字重'
    wrap_char_num = len(txt)
    while (size := ft.getbbox(txt[0:wrap_char_num]))[2] > max_x:
        if wrap_char_num > 2:
            wrap_char_num -= 2
        else:
            raise ValueError(f'最大宽度{max_x}设定太小！')

    r_num = math.ceil(len(txt)/wrap_char_num)
    tmp_img = Image.new('RGB', [size[2], size[3] * r_num], bg_color)
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

def table_draw(table: list[list], ft: ImageFont.FreeTypeFont, max_column_x: int = 400, 
               colors: tuple[int|tuple[int]] = (0xffffff, 0xf6f8fa), margin: tuple[int] = (8, 4)):
    img_table: list[list[Image.Image]] = []
    c_width_list: list[int] = []
    r_height_list: list[int] = []
    for column in table:
        img_table.append([])
        c_width = 0
        for txt in column:
            #获取单列最大宽度，不得超过max_column_x
            if (size := ft.getbbox(txt))[2] > max_column_x:
                c_width = max_column_x
                break
            else:
                if size[2] > c_width:
                    c_width = size[2]
        c_width_list.append(c_width)
    #生成文字对应图片放入img_table
    for c_no in range(len(table)):
        color_p = -1
        for txt in table[c_no]:
            if color_p == -1:
                t_color_p = 0
            else:
                t_color_p = color_p
            
            img_table[c_no].append(txt_draw(txt, ft, c_width, bg_color=colors[t_color_p]))
            color_p = (color_p + 1) % 2


    #获取每行的高度
    for r_no in range(len(table[0])):
        r_height = 0
        for c_no in range(len(table)):
            if img_table[c_no][r_no].size[1] > r_height:
                r_height = img_table[c_no][r_no].size[1]
        r_height_list.append(r_height)
    
    for c_no in range(len(table)):
        color_p = -1
        for r_no in range(len(table[0])):
            if color_p == -1:
                t_color_p = 0
            else:
                t_color_p = color_p
            img_table[c_no][r_no] = img_box(img_expand(img_table[c_no][r_no], 
                                               [c_width_list[c_no] + margin[0]*2, r_height_list[r_no] + margin[1]*2],
                                               colors[t_color_p]))

    imgs_per_column = []
    for c_imgs in img_table:
        imgs_per_column.append(img_stack_v(c_imgs, -2, (0, 0, 0, 0)))
    return img_stack_h(imgs_per_column, -2, (0, 0, 0, 0))

def img_expand(img: Image.Image, target_size: tuple[int] = (-1, -1), bg_color: tuple[int]|int = 0xffffff, align: str = 'center') -> Image.Image:
    this_x, this_y = img.size
    new_x = 0
    new_y = 0
    if this_x < target_size[0]:
        new_x = target_size[0]
    else:
        new_x = this_x

    if this_y < target_size[1]:
        new_y = target_size[1]
    else:
        new_y = this_y

    if new_x == this_x and new_y == this_y:
        return img
    
    n_img = Image.new('RGB', [new_x, new_y], bg_color)

    pos_x = 0
    pos_y = int((new_y - this_y)/2)

    if align == 'left':
        pass
    elif align == 'center':
        pos_x = int((new_x - this_x)/2)
    elif align == 'right':
        pos_x = new_x - this_x

    n_img.paste(img, [pos_x, pos_y])
    return n_img

def img_box(img: Image.Image, box_width: int = 2, box_color: tuple[int]|int = 0xd0d7de) -> Image.Image:
    this_x, this_y = img.size
    n_img = Image.new('RGB', [this_x + box_width*2, this_y + box_width*2], box_color)
    n_img.paste(img, [box_width, box_width])
    return n_img

def img_stack_v(imgs: list[Image.Image|str], margin_line: int = 5, margin_border: tuple[int] = (20, 20, 10, 10), align: str = 'center') -> Image.Image:
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
            img_y += (2 + margin_line)
        elif i == 'space':
            img_y += (8 + margin_line)
        else:
            continue

    img_y -= margin_line

    a_img = Image.new('RGB', [img_x + margin_border[0] + margin_border[1], img_y + margin_border[2] + margin_border[3]], 0xffffff)
    y_shift = 0
    for i in range(len(imgs)):
        tmp_img = imgs[i]
        if isinstance(tmp_img, str):
            #特殊字符处理
            if tmp_img== 'line':
                tmp_img = Image.new('RGB', [img_x, 2], 0xd0d7de)
            elif tmp_img == 'space':
                y_shift += (8 + margin_line)
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

def img_to_BytesIO(img: Image.Image, quality: int = 95, dpi: tuple[int] = (100, 100)) -> io.BytesIO:
    tmp_io = io.BytesIO()
    img.save(tmp_io, format='JPEG', quality = quality, dpi = dpi)
    return tmp_io










