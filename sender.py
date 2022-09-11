from __future__ import annotations
import configparser
import io
from math import ceil
import traceback
import requests
import time
import os
import json
import logging
import re
from PIL import Image

from util.logger import init_logger

log_path = os.path.join(os.path.dirname(__file__), "logs", "sender")
logger: logging.Logger = init_logger(log_path)
cf = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=["#"], comment_prefixes=["#"])
cf.read(f"config.ini", encoding="UTF-8")
http_url = cf.get("cqhttp", "http_url")
local_pic_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_pic")

def send_guild_channel_msg(message):
    resp = requests.post(f"{http_url}/send_guild_channel_msg", data = message, headers={'Connection':'close'})
    return resp

def send_message():
    with open("msg_para", "r", encoding="UTF-8") as f:
        message = json.loads(f.read())
        message['message'] = "".join(message['data'])
    try:
        response = send_guild_channel_msg(message)
        logger.debug(f"成功发送消息请求，返回值：{response.text}")
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"发送消息失败，错误信息：{str(e)}\n消息内容：\n{json.dumps(message, ensure_ascii=False)}")
        os._exit(-1)

def is_success(response):
    if(response['retcode'] == 0):
        return not response['data']['message_id'].startswith('0-')
    else:
        return False

def replace_pic(matched: re.Match):
    global pic_count
    pic_url: str = matched.group(1)
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
    }
    pic_count += 1
    try:
        pic_path = os.path.join(local_pic_path, f'{pic_count}.png')
        if(pic_url.startswith("file:///")):
            with open(pic_url[8:len(pic_url):], "rb") as f:
                pic = f.read()
        else:
            pic = requests.get(pic_url, headers=headers, timeout=15)
            pic = pic.content
        pic = modify_pic(pic)
        pic.save(pic_path)
    except:
        errmsg = traceback.format_exc()
        logger.error(f"获取网络图片发生错误，图片地址：{pic_url}，错误信息如下：\n{errmsg}")
        return "[图片获取失败]"
    return f"[CQ:image,file=file:///{pic_path}]"

def process_pic():
    global pic_count
    pic_count = 0
    os.makedirs(local_pic_path, exist_ok=True)
    with open("msg_para", "r", encoding="UTF-8") as f:
        message = json.loads(f.read())
    for i in range(len(message['data'])):
        message['data'][i] = re.sub(r"\[CQ:image,file=(\S+)?\]", replace_pic, message['data'][i])
    with open("msg_para", "w", encoding="UTF-8") as f:
        f.write(json.dumps(message))

def modify_pic(pic: bytes) -> Image.Image:
    pic = Image.open(io.BytesIO(pic))
    res = Image.new("RGBA", (pic.size[0], pic.size[1] + 1), color=(0,0,0,0))
    res.paste(pic, box=(0,0))
    return compress_pic(res)

def compress_pic(image: Image.Image, compress_cnt: int = 1) -> bytes:
    while(compress_cnt > 0):
        image = image.resize((ceil(image.size[0] / 1.5), ceil(image.size[1] / 1.5)), Image.ANTIALIAS)
        compress_cnt -= 1
    return image

if __name__ == '__main__':
    cnt = 1
    response = send_message()
    while(cnt < 3 and (not is_success(response))):
        time.sleep(0.03)
        response = send_message()
        cnt = cnt + 1
    if response['retcode'] == 0 and response['data']['message_id'].startswith('0-'):
        process_pic()
        cnt = 1
        response = send_message()
        while(cnt < 3 and (not is_success(response))):
            time.sleep(0.03)
            response = send_message()
            cnt = cnt + 1
