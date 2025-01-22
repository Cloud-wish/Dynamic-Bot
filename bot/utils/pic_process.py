from __future__ import annotations
import io
import os
import httpx
from math import ceil
from PIL import Image, ImageFont, ImageDraw
from fontTools.ttLib import TTFont

font_path_list = [
    "msyh.ttc",
    "notocoloremoji.ttf",
    "unifont.ttf"
]
font_path_list = [os.path.join(os.getcwd(), "fonts", font_path) for font_path in font_path_list]
judge_font_list = [TTFont(font_path, fontNumber=0) for font_path in font_path_list]
draw_font_list: list[ImageFont.FreeTypeFont] = []
for font_path in font_path_list:
    draw_font_list.append(ImageFont.truetype(font_path, size=109))

def join_pic(img_1: bytes, img_2: bytes, flag: str = 'y', fmt: str = "jpeg"):
    img1 = Image.open(io.BytesIO(img_1))
    img2 = Image.open(io.BytesIO(img_2))
    size1, size2 = img1.size, img2.size
    if flag == 'x':
        joint = Image.new("RGB", (size1[0] + size2[0], max(size1[1], size2[1])), (255,255,255))
        loc1, loc2 = (0, 0), (size1[0], 0)
    else:
        joint = Image.new("RGB", (max(size1[0], size2[0]), size2[1]+size1[1]), (255,255,255))
        loc1, loc2 = (0, 0), (0, size1[1])
    joint.paste(img1, loc1)
    joint.paste(img2, loc2)
    output = io.BytesIO()
    joint.save(output, format=fmt)
    return output.getvalue()

def modify_pic(pic: bytes) -> bytes:
    image = Image.open(io.BytesIO(pic))
    width = image.size[0]
    height = image.size[1]
    scale = 2
    if((width/height) > scale):
        res = Image.new(mode = 'RGB', size=(width, int(width/scale)+1), color = (255, 255, 255))
        res.paste(image, (0,int((res.height - height)/2)))
        # if(res.size[0] > 1000):
        #     scale = 1000/res.size[0]
        #     res = res.resize((int(res.size[0]*scale), int(res.size[1]*scale)), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        res.save(output, format="jpeg")
        return output.getvalue()
    else:
        return pic

def compress_pic(pic: bytes, compress_cnt: int = 1) -> bytes:
    image = Image.open(io.BytesIO(pic))
    image = image.convert('RGB')
    while(compress_cnt > 0):
        image = image.resize((ceil(image.size[0] / 1.5), ceil(image.size[1] / 1.5)), Image.Resampling.LANCZOS)
        compress_cnt -= 1
    output = io.BytesIO()
    image.save(output, format="jpeg")
    return output.getvalue()

def save_pic(pic: bytes, pic_path: str) -> bool:
    os.makedirs(os.path.dirname(pic_path), exist_ok=True)
    with open(pic_path, "wb") as f:
        f.write(pic)
    return True

def has_glyph_font(glyph) -> int:
    for i in range(len(judge_font_list)):
        for table in judge_font_list[i]['cmap'].tables:
            if ord(glyph) in table.cmap.keys():
                return i
    return len(judge_font_list) - 1

def extend_pic(img_upper: Image.Image, extend_height: int, bg_color: str) -> Image.Image:
    img_new = Image.new("RGB", (img_upper.size[0], img_upper.size[1] + extend_height), bg_color)
    img_new.paste(img_upper, box=(0,0))
    # img_new.show()
    return img_new

def input_pic_textbox(img: Image.Image, draw: ImageDraw.ImageDraw, xy: list[tuple[int]], raw_text: str, color: str, font_list: list[ImageFont.FreeTypeFont], bg_color: str, mode: str = "left"):
    raw_text = raw_text.replace("\r", "")
    box_width = xy[1][0] - xy[0][0]
    box_height = xy[1][1] - xy[0][1]
    line_text: list[str] = [""]
    line_height: list[int] = [0]
    line_width: list[int] = [0]
    total_height: int = 0
    cur_line = 0
    # print(raw_text, box_width)
    for i, c in enumerate(raw_text):
        font = font_list[has_glyph_font(c)]
        c_size = draw.textbbox((0,0), c, font)[2:4:]
        if(line_width[cur_line] + c_size[0] >= box_width or c == "\n"):
            # print(line_text[cur_line], line_height[cur_line], line_width[cur_line])
            cur_line += 1
            line_width.append(0)
            line_height.append(0)
            line_text.append("")
        line_width[cur_line] += c_size[0]
        if not (c == "\n" and i+1 < len(raw_text) and raw_text[i+1] != "\n"):
            line_height[cur_line] = max(line_height[cur_line], c_size[1])
        line_text[cur_line] += c
    for height in line_height:
        total_height += height
    if(total_height > box_height):
        img = extend_pic(img, total_height - box_height, bg_color)
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
            c_size = draw.textbbox((0,0), c, font)[2:4:]
            draw.text((xy[0][0] + cur_x, xy[0][1] + cur_y), c, font=font, fill=color, embedded_color=True)
            cur_x += c_size[0]
        cur_y += line_height[i]
    return (img, draw, total_height + xy[0][1])

def print_text_on_pic(img: Image.Image, height: int, text: str) -> tuple[Image.Image, int]:
    draw = ImageDraw.Draw(img)
    upper_left = (0, height)
    lower_right = img.size
    img, draw, res_height = input_pic_textbox(img, draw, [upper_left, lower_right], text, "black", draw_font_list, "white")
    return (img, res_height)

def print_img_on_pic(img: Image.Image, height: int, input_img: bytes) -> tuple[Image.Image, int]:
    input_img: Image.Image = Image.open(io.BytesIO(input_img))
    added_height = input_img.size[1]
    if height + added_height > img.size[1]:
        img = extend_pic(img, height+added_height-img.size[1], "white")
    img.paste(input_img, box=(0,height))
    return (img, height+added_height)

def resize_pic(img: Image.Image, width: int = None, height: int = None, scale: float = None) -> Image.Image:
    if width:
        scale = width / img.size[0]
    elif height:
        scale = height / img.size[1]
    img = img.resize((ceil(img.size[0] * scale), ceil(img.size[1] * scale)), Image.Resampling.LANCZOS)
    return img

def img_to_bytes(img: Image.Image, fmt: str = "jpeg") -> bytes:
    output = io.BytesIO()
    if fmt != "png" and img.mode == "RGBA":
        img = img.convert("RGB")
    img.save(output, format=fmt)
    return output.getvalue()

def horizontal_padding_pic(img: Image.Image, extend_width: int, bg_color: str, center: bool = True) -> Image.Image:
    width = img.size[0]
    height = img.size[1]
    res = Image.new(mode = 'RGB', size=(width + extend_width, height), color = bg_color)
    res.paste(img, (int(extend_width/2),0))
    return res

def print_on_pic(msg_list: list[dict]) -> bytes:
    width = 3000
    final_width = 1000
    scale = final_width/width
    img = Image.new("RGB", (width, 500), "white")
    height = 0
    pic_list: list[dict] = []
    for msg in msg_list:
        if msg["type"] == "text":
            img, height = print_text_on_pic(img, height, msg["content"])
        else:
            try:
                msg["content"] = Image.open(io.BytesIO(msg["content"]))
            except:
                img, height = print_text_on_pic(img, height, "[图片加载失败]")
                continue
            if msg.get("para", {}).get("extend_width", False):
                msg["content"] = resize_pic(msg["content"], width=final_width)
            else:
                msg["content"] = resize_pic(msg["content"], width=ceil(final_width*0.7))
            pic_list.append({
                "pic": msg["content"],
                "height": ceil(height*scale) + 20
            })
            height += ceil(msg["content"].size[1]/scale) + 20 + 20
    img = resize_pic(img, width=final_width)
    for pic in pic_list:
        if(pic["pic"].size[1] + pic["height"] > img.size[1]):
            img = extend_pic(img, pic["pic"].size[1]+pic["height"]-img.size[1], "white")
        img.paste(pic["pic"], (0,pic["height"]))
    img = horizontal_padding_pic(img, 60, "white")
    return img_to_bytes(img)

async def download_pic(url: str, headers: dict = None) -> bytes:
    if not headers:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
        }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url=url, headers=headers)
    return resp.content