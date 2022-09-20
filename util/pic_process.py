import io
from math import ceil
import os
from PIL import Image

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
    if((width/height) > 3):
        res = Image.new(mode = 'RGB', size=(width, int(width/3)+1), color = (255, 255, 255))
        res.paste(image, (0,int((res.height - height)/2)))
        output = io.BytesIO()
        res.save(output, format="jpeg")
        return output.getvalue()
    else:
        return pic

def compress_pic(pic: bytes, compress_cnt: int = 1) -> bytes:
    image = Image.open(io.BytesIO(pic))
    image = image.convert('RGB')
    while(compress_cnt > 0):
        image = image.resize((ceil(image.size[0] / 1.5), ceil(image.size[1] / 1.5)), Image.ANTIALIAS)
        compress_cnt -= 1
    output = io.BytesIO()
    image.save(output, format="jpeg")
    return output.getvalue()

def save_pic(pic: bytes, pic_path: str) -> bool:
    os.makedirs(os.path.dirname(pic_path), exist_ok=True)
    with open(pic_path, "wb") as f:
        f.write(pic)
    return True