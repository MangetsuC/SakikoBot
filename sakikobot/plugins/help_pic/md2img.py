from .draw import *
from PIL import Image, ImageDraw, ImageFont

class Markdown_decoder:
    def __init__(self, base_font: ImageFont.FreeTypeFont, 
                 txt: str = '', file_abs_root: str = '.', 
                 size: list[int] = [60, 45, 35, 25]) -> None:
        self.txt = txt
        self.file_abs_root = file_abs_root
        self.size = size
        self.base_font = base_font

    def build(self) -> Image.Image:
        img_stack = []
        for l in self.decode_wrap(self.txt):
            if l == '\n':
                #img_stack.append('space')
                continue

            t = self.check_title(l)
            if isinstance(t, dict):
                level = t['level']
                img_stack.append(txt_draw(t['txt'], set_font_size(self.base_font, self.size[level - 1]), f_weight='thin'))
                if level == 1:
                    img_stack.append(f'line 4')
                elif level == 2:
                    img_stack.append(f'line 2')
            else:
                pics_t = self.check_pic(l)
                tmp_h_img_stack = []
                for p in pics_t:
                    if isinstance(p, dict):
                        tmp_h_img_stack.append(Image.open(p['path']).convert('RGB'))
                    elif isinstance(p, str):
                        tmp_h_img_stack.append(txt_draw(p, set_font_size(self.base_font, self.size[3])))
                if len(tmp_h_img_stack) > 1:
                    img_stack.append(img_stack_h(tmp_h_img_stack, margin_line= 0, margin_border= [0,0,0,0]))
                else:
                    img_stack.append(tmp_h_img_stack[0])

        return img_stack_v(img_stack)


    def decode_wrap(self, md_txt: str) -> list[str]:
        md_list = md_txt.split('\n')
        ans = []
        tmp_str = []

        for l in md_list:
            if l:
                tmp_str.append(l)
            else:
                ans.append(' '.join(tmp_str))
                tmp_str.clear()
                ans.append('\n')
        else:
            ans.append(' '.join(tmp_str))
        return ans

    def check_title(self, txt: str) -> dict|str:
        tmp_txt = txt.strip(' ')
        title_level = 0
        if tmp_txt[0] == '#':
            for i in tmp_txt:
                if i == '#':
                    title_level += 1
                else:
                    break
            real_txt = tmp_txt[title_level:]
            if title_level > 3:
                title_level = 3
            return dict(var = 'title', level = title_level, txt = real_txt)
        return txt

    def check_pic(self, txt: str) -> list:
        ans = []
        after_pic_end = 0
        i = 0
        while i < len(txt) - 1:
        #for i in range(0, len(txt) - 1):
            if txt[i] == '!':
                if txt[i+1] == '[':
                    pos_right_s_bracket = -1
                    for j in range(i+1, len(txt)):
                        if txt[j] == ']':
                            pos_right_s_bracket = j
                            break
                    if pos_right_s_bracket > 0:
                        if txt[pos_right_s_bracket + 1] == '(':
                            pos_right_c_bracket = -1
                            for j in range(pos_right_s_bracket + 2, len(txt)):
                                if txt[j] == ')':
                                    pos_right_c_bracket = j
                                    break
                            if pos_right_c_bracket > 0:
                                #i为开头感叹号的位置, pos_right_s_bracket+1为左圆括号, pos_right_c_bracket为右圆括号
                                if after_pic_end < i:
                                    ans.append(txt[after_pic_end:i])
                                pic_path = txt[pos_right_s_bracket+2:pos_right_c_bracket].strip(' ').split(' ')[0].strip(' \'"')
                                if len(pic_path) > 2:
                                    if pic_path[0:2] == './':
                                        pic_path = f'{self.file_abs_root}/{pic_path[2:]}'

                                ans.append(dict(var = 'pic', path = pic_path))
                                after_pic_end = pos_right_c_bracket + 1
                                i = pos_right_c_bracket
            
            i += 1
        if after_pic_end + 1 < len(txt):
            ans.append(txt[after_pic_end:])
        
        return ans

    @classmethod
    def load(cls, path: str, font: ImageFont.FreeTypeFont):
        with open(path, 'r', encoding='utf-8') as f:
            txt = f.read()
        return cls(font, txt, '/'.join(path.split('/')[:-1]))








