from .draw import *
from PIL import Image, ImageDraw, ImageFont
import os

class Markdown_decoder:
    def __init__(self, base_font: ImageFont.FreeTypeFont, 
                 txt: str = '', file_abs_root: str = '.', 
                 size: list[int] = [60, 50, 40, 30, 25, 20, 25]) -> None:
        self.txt = txt
        self.file_abs_root = file_abs_root
        self.size = size
        self.base_font = base_font

    def build(self, align = 'center') -> Image.Image:
        img_stack = []
        wraped_txt = self.decode_wrap(self.txt)
        wraped_txt_len = len(wraped_txt)
        l_num = 0
        is_added_space = False #多次换行只添加一次间隔
        while l_num < wraped_txt_len:
        #for l_num in :
            l = wraped_txt[l_num]
            cached_l_num = l_num
            l_num += 1

            if l == '\n':
                if not is_added_space:
                    img_stack.append('space')
                if l_num == wraped_txt_len:
                    img_stack.pop()
                continue
            is_added_space = False

            #解析
            l = self.check_title(l)
            l = self.check_table(l)
            l = self.check_indent(l)
            l = self.check_pic(l)

            #绘制
            if isinstance(l, dict):
                if l['var'] == 'title':
                    level = l['level']
                    if level >= 5:
                        f_color = 0x262626
                    else:
                        f_color = 0x000000
                    img_stack.append(txt_draw(l['txt'], set_font_size(self.base_font, self.size[level - 1]), color=f_color))
                    if level <= 4:
                        img_stack.append('line')
                    continue
                elif l['var'] == 'table':
                    txt_list = l['datas']
                    img_stack.append(table_draw(txt_list, set_font_size(self.base_font, self.size[6])))
                    continue
                elif l['var'] == 'indent':
                    txt_list = l['lines']
                    indent_tmp_img_stack = []
                    for t in txt_list:
                        indent_tmp_img_stack.append(txt_draw(t, set_font_size(self.base_font, self.size[6]), color=0x766d67))
                    img_stack.append(img_stack_h(['line 6', img_stack_v(indent_tmp_img_stack)], 0, (0, 0, 0, 0)))
                    continue
                elif l['var'] == 'pic':
                    if os.path.exists(l['path']):
                        img_stack.append(Image.open(l['path']).convert('RGB'))
                    else:
                        img_stack.append(txt_draw(f'[{l["alt"]}]', set_font_size(self.base_font, self.size[6])))
                    continue
            elif isinstance(l, list):
                tmp_h_img_stack = []
                for p in l:
                    if isinstance(p ,str):
                        tmp_h_img_stack.append(txt_draw(l.replace('%bk%', ' ').strip(' '), 
                                          set_font_size(self.base_font, self.size[5])))
                    elif isinstance(p, dict):
                        if p['var'] == 'title':
                            level = p['level']
                            tmp_h_img_stack.append(txt_draw(p['txt'], set_font_size(self.base_font, self.size[level - 1])))
                            tmp_h_img_stack.append('line')
                        elif p['var'] == 'table':
                            txt_list = l['datas']
                            tmp_h_img_stack.append(table_draw(txt_list, set_font_size(self.base_font, self.size[6])))
                            continue
                        elif l['var'] == 'indent':
                            txt_list = l['lines']
                            indent_tmp_img_stack = []
                            for t in txt_list:
                                indent_tmp_img_stack.append(txt_draw(t, set_font_size(self.base_font, self.size[6]), color=0x766d67))
                            tmp_h_img_stack.append(img_stack_h(['line 6', img_stack_v(indent_tmp_img_stack)], 0, (0, 0, 0, 0)))
                        elif p['var'] == 'pic':
                            if os.path.exists(p['path']):
                                tmp_h_img_stack.append(Image.open(p['path']).convert('RGB'))
                            else:
                                tmp_h_img_stack.append(txt_draw(f'[{p["alt"]}]', set_font_size(self.base_font, self.size[6])))
                if len(tmp_h_img_stack) > 1:
                    img_stack.append(img_stack_h(tmp_h_img_stack, margin_line= 0, margin_border= [0,0,0,0]))
                else:
                    img_stack.append(tmp_h_img_stack[0])
                continue
            elif isinstance(l, str):
                img_stack.append(txt_draw(l.replace('%bk%', ' ').strip(' '), 
                                          set_font_size(self.base_font, self.size[6])))
                continue
            else:
                continue

        return img_stack_v(img_stack, align=align)


    def decode_wrap(self, md_txt: str) -> list[str]:
        md_list = md_txt.split('\n')
        ans = []
        tmp_str = []

        for l in md_list:
            if l:
                tmp_str.append(l.strip(' '))
            else:
                if tmp_str:
                    ans.append('%bk%'.join(tmp_str))
                    tmp_str.clear()
                ans.append('\n')
        else:
            if tmp_str:
                ans.append('%bk%'.join(tmp_str))
        return ans

    def check_title(self, txt: str) -> dict|str|list:
        if isinstance(txt, dict):
            return txt
        elif isinstance(txt, list):
            for t in txt:
                tmp = []
                tmp.append(self.check_title(t))
                return tmp
            
        tmp_txt = txt.replace('%bk%', ' ').strip(' ')
        title_level = 0
        if tmp_txt[0] == '#':
            for i in tmp_txt:
                if i == '#':
                    title_level += 1
                else:
                    break
            real_txt = tmp_txt[title_level:]
            if title_level > 6:
                title_level = 6
            return dict(var = 'title', level = title_level, txt = real_txt.strip(' '))
        return txt
    
    def check_table(self, txt: str) -> str|dict|list:
        if isinstance(txt, dict):
            return txt
        elif isinstance(txt, list):
            for t in txt:
                tmp = []
                tmp.append(self.check_table(t))
                return tmp
        
        txt_list = txt.split('%bk%')
        tmp_t = txt_list[0].strip(' ')
        if tmp_t[0] == '|' and tmp_t[-1] == '|':
            table: list[list] = []
            for c_txt in tmp_t.split('|'):
                if c_content:= c_txt.strip(' '):
                    table.append([c_content])

            n_line_num = 1
            while n_line_num < len(txt_list):
                n_txt = txt_list[n_line_num]
                n_tmp_t = n_txt.strip(' ')
                n_line_num += 1 #检索需要跳过的行

                if n_tmp_t[0] == '|' and n_tmp_t[-1] == '|':
                    is_only_hyphen = True
                    tmp_t_split = n_tmp_t.split('|')
                    for n_c_txt in tmp_t_split:
                        if n_c_content:= n_c_txt.strip(' '):
                            for char in n_c_content:
                                if char != '-' and char != ':':
                                    is_only_hyphen = False
                                    break
                            if not is_only_hyphen:
                                break
                    if not is_only_hyphen: #不是标题分隔栏
                        t_index = 0
                        for n_c_txt in tmp_t_split:
                            if n_c_content:= n_c_txt.strip(' '):
                                table[t_index].append(n_c_content)
                                t_index += 1
                else:
                    break
            return dict(var = 'table', datas = table)

        return txt
    
    def check_indent(self, txt: str) -> list|dict|str:
        if isinstance(txt, dict):
            return txt
        elif isinstance(txt, list):
            for t in txt:
                tmp = []
                tmp.append(self.check_indent(t))
                return tmp
            
        tmp_t = txt.strip(' ')
        if tmp_t and tmp_t[0] == '>':
            txt_list = tmp_t.split('%bk%')
            indent_list = []
            tmp_txt_list = []
            for t in txt_list:
                this_line_t = t.strip(' >')
                if this_line_t:
                    tmp_txt_list.append(this_line_t)
                else:
                    if tmp_txt_list:
                        indent_list.append(' '.join(tmp_txt_list))
                        tmp_txt_list.clear()
            else:
                if tmp_txt_list:
                    indent_list.append(' '.join(tmp_txt_list))
            
            if indent_list:
                return dict(var = 'indent', lines = indent_list)


        return txt


    def check_pic(self, txt: str) -> list|dict|str:
        if isinstance(txt, dict):
            return txt
        elif isinstance(txt, list):
            for t in txt:
                tmp = []
                tmp.append(self.check_pic(t))
                return tmp

        ans = []
        after_pic_end = 0
        i = 0
        #is_pic = False
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
                                        pic_path = f'{self.file_abs_root}/{pic_path[2:pos_right_s_bracket].strip(" ")}'

                                ans.append(dict(var = 'pic', path = pic_path, alt = txt[i+2:pos_right_s_bracket]))
                                #is_pic = True
                                after_pic_end = pos_right_c_bracket + 1
                                i = pos_right_c_bracket
            
            i += 1
        if after_pic_end + 1 < len(txt):
            ans.append(txt[after_pic_end:])

        if len(ans) == 1:
            ans = ans[0]
        
        return ans

    @classmethod
    def load(cls, path: str, font: ImageFont.FreeTypeFont):
        with open(path, 'r', encoding='utf-8') as f:
            txt = f.read()
        return cls(font, txt, '/'.join(path.split('/')[:-1]))








