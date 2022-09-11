from __future__ import annotations
import configparser
import copy
import logging
import jsons
import platform
import os

from PIL import Image, ImageFont, ImageDraw
from fontTools.ttLib import TTFont

logger = logging.getLogger("dynamic-bot")
sys_str = platform.system()
font_path_list = [
    "msyh.ttc",
    "unifont.ttf"
]
font_path_list = [os.path.join(os.getcwd(), "font", font_path) for font_path in font_path_list]
judge_font_list = [TTFont(font_path, fontNumber=0) for font_path in font_path_list]
draw_font_list: list[ImageFont.FreeTypeFont] = [ImageFont.truetype(font_path, size=26, encoding="unic") for font_path in font_path_list]
pic_save_path = os.path.join(os.getcwd(), "temp", "message_pic.png")
os.makedirs(os.path.dirname(pic_save_path), exist_ok=True)
cf = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=["#"], comment_prefixes=["#"])
cf.read(f"config.ini", encoding="UTF-8")
sender_command = cf.get("sender", "python_exec_command")

def do_send_msg(msg: dict, cmd: str):
    with open("msg_para", "w", encoding="UTF-8") as f:
        f.write(jsons.dumps(msg))
    if(sys_str == "Linux"):
        code = os.WEXITSTATUS(os.system(cmd))
    else:
        code = os.system(cmd)
    return code == 0

def has_glyph_font(glyph) -> int:
    for i in range(len(judge_font_list)):
        for table in judge_font_list[i]['cmap'].tables:
            if ord(glyph) in table.cmap.keys():
                return i
    return len(judge_font_list) - 1

def pic_extend(img_upper: Image.Image, extend_height: int, bg_color: str) -> Image.Image:
    img_new = Image.new("RGBA", (img_upper.size[0], img_upper.size[1] + extend_height), bg_color)
    img_new.paste(img_upper, box=(0,0))
    # img_new.show()
    return img_new

def pic_input_textbox(img: Image.Image, draw: ImageDraw.ImageDraw, xy: list[tuple[int]], raw_text: str, color: str, font_list: list[ImageFont.FreeTypeFont], bg_color: str, mode: str = "left"):
    raw_text = raw_text.replace("\r", "")
    box_width = xy[1][0] - xy[0][0]
    box_height = xy[1][1] - xy[0][1]
    line_text: list[str] = [""]
    line_height: list[int] = [0]
    line_width: list[int] = [0]
    total_height: int = 10 # 余量
    cur_line = 0
    # print(raw_text, box_width)
    for c in raw_text:
        font = font_list[has_glyph_font(c)]
        c_size = draw.textsize(c, font)
        if(line_width[cur_line] + c_size[0] >= box_width or c == "\n"):
            # print(line_text[cur_line], line_height[cur_line], line_width[cur_line])
            cur_line += 1
            line_width.append(0)
            line_height.append(0)
            line_text.append("")
            if(c == "\n"):
                c_size = (c_size[0], 10)
        line_width[cur_line] += c_size[0]
        line_height[cur_line] = max(line_height[cur_line], c_size[1])
        line_text[cur_line] += c
    for height in line_height:
        total_height += height
    if(total_height > box_height):
        img = pic_extend(img, total_height - box_height, bg_color)
        draw = ImageDraw.Draw(img)
    cur_y = 0
    for i in range(len(line_text)):
        if(mode == "left"):
            cur_x = 0
        elif(mode == "center"):
            cur_x = (box_width - line_width[i])/2
        elif(mode == "right"):
            cur_x = (box_width - line_width[i])
        for c in line_text[i]:
            font = font_list[has_glyph_font(c)]
            draw.text((xy[0][0] + cur_x, xy[0][1] + cur_y), c, font=font, fill=color)
            cur_x += draw.textsize(c, font)[0]
        cur_y += line_height[i]
    return (img, draw)

def get_text_pic(raw_texts: list[str]) -> list[str]:
    texts = []
    pics = []
    for text in raw_texts:
        if(not text.startswith('[CQ:image')):
            texts.append(text)
        else:
            texts.append("[图片]")
            pics.append(text)
    img = Image.new("RGBA", (600, 150), 'white')
    img_draw = ImageDraw.Draw(img)
    img, img_draw = pic_input_textbox(img, img_draw, [(0,0),(600,150)], "".join(texts), "black", draw_font_list, "white")
    img.save(pic_save_path)
    return [f"[CQ:image,file=file:///{pic_save_path}]"] + pics

def send_guild_msg(msg: dict):
    if(do_send_msg(msg, f"{sender_command} sender.py")):
        return
    logger.info("消息发送失败，尝试加空格")
    for i in range(len(msg['data'])):
        if(msg['data'][i] != "\n"):
            # 深复制
            _msg = copy.deepcopy(msg)
            _msg['data'][i] = _msg['data'][i] + " "
            logger.debug(f"尝试在第{i}个字符串后加空格")
            if(do_send_msg(msg, f"{sender_command} sender.py")):
                return
    logger.info("消息发送失败，尝试转换为图片")
    _msg = copy.deepcopy(msg)
    _msg['data'] = get_text_pic(_msg['data'])
    if(do_send_msg(msg, f"{sender_command} sender.py")):
        return
    logger.error(f"无法发送频道{msg['guild_id']}的子频道{msg['channel_id']}的消息，详情已记录在sender日志，消息内容：\n{''.join(msg['data'])}")
    

