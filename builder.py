from __future__ import annotations
import configparser
import copy
from datetime import datetime, timedelta, timezone
import logging
import json
import os
import traceback
import httpx

from util.bot_command import cmd
from util.pic_builder import PicBuilder
from util.pic_process import modify_pic, save_pic
from constant import type_dict

_type_dict = copy.deepcopy(type_dict)
_type_dict["bili_dyn"] = "B站"

logger = logging.getLogger("dynamic-bot")
cf = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=["#"], comment_prefixes=["#"])
cf.read(f"config.ini", encoding="UTF-8")
pic_enable = cf.getboolean("builder", "pic_enable")
for name, section in cf.items():
    if name == "builder":
        pic_config_dict = dict()
        for key, value in section.items():
            try:
                value = int(value)
            except:
                pass
            if(value == "true"):
                value = True
            elif(value == "false"):
                value = False
            pic_config_dict[key] = value
        pic_config_dict["pic_save_path"] = os.path.abspath(pic_config_dict["pic_save_path"])
        pic_builder = PicBuilder(pic_config_dict)
        break

uid_to_name_dict = None
push_pic_config_dict = {}

try:
    with open("uid_to_name.json", "r", encoding="UTF-8") as f:
        uid_to_name_dict = json.loads(f.read())
except:
    pass
try:
    with open("push_pic_config.json", "r", encoding="UTF-8") as f:
        push_pic_config_dict = json.loads(f.read())
except:
    pass

weibo_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    "Referer": "https://m.weibo.cn/"
}

def data_preprocess(data: dict, typ: str) -> dict:
    global uid_to_name_dict
    if("created_time" in data and type(data["created_time"]) == int):
        data["created_time"] = datetime.fromtimestamp(data["created_time"], tz=timezone(timedelta(hours=+8))).strftime("%Y-%m-%d %H:%M:%S")
    if uid_to_name_dict:
        user = data.get("user", {})
        if "name" in user:
            if user.get("uid", "") in uid_to_name_dict[typ]:
                data["user"]["name"] = uid_to_name_dict[typ][data["user"]["uid"]]
        else:
            data["user"]["name"] = "[未知用户名]"
    if("retweet" in data):
        data["retweet"] = data_preprocess(data["retweet"], typ)
    if("reply" in data):
        data["reply"] = data_preprocess(data["reply"], typ)
    return data

async def download_image(url: str, headers: dict = None) -> bytes:
    if not headers:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
        }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url=url, headers=headers)
    return resp.content

@cmd(("avatar", ))
async def avatar_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: list[str] = []
    content.append(f"{data['user']['name']}更换了{_type_dict[data['type']]}头像：\n")
    if data['type'] == "weibo" and pic_config_dict["weibo_avatar_save"]:
        pic_path = os.path.join(pic_config_dict["pic_save_path"], "weibo", "avatar", f"{uid}.jpeg")
        save_pic(await download_image(data["now"], weibo_headers), pic_path)
        content.append('[CQ:image,file=file:///'+pic_path+']')
    else:
        content.append('[CQ:image,file='+data["now"]+']')
    return content

@cmd(("desc", ))
async def desc_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: list[str] = []
    content.append(f"{data['user']['name']}更改了{_type_dict[data['type']]}简介：\n")
    content.append(data["now"])
    return content

@cmd(("name", ))
async def name_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: list[str] = []
    content.append(f"{data['pre']}更改了{_type_dict[data['type']]}用户名：")
    content.append(data["now"])
    return content

@cmd(("weibo", ))
async def weibo_pic_builder(subtype: str, uid: str, data: dict) -> list[str]:
    if not pic_enable:
        return None
    push_dict = push_pic_config_dict.get(data["type"], {}).get(subtype, {})
    if not (len(data.get("pics", [])) >= pic_config_dict["weibo_pics_limit"] or ("retweet" in data and len(data['retweet'].get("pics", [])) >= pic_config_dict["weibo_pics_limit"])):
        if not (uid in push_dict.get("enable", []) or push_dict.get("enable", "") == "all"):
            return None
    elif uid in push_dict.get("disable", []) or push_dict.get("disable", "") == "all":
        return None

    content: list[str] = []
    if("retweet" in data):
        content.append(f"{data['user']['name']}在{data['created_time']}转发了{data['retweet']['user']['name']}的微博并说：\n")
    else:
        content.append(f"{data['user']['name']}在{data['created_time']}发了新微博并说：\n")
    for i in range(3):
        try:
            pic = await pic_builder.get_wb_pic(data["id"], data["created_time"])
            break
        except:
            if i == 2:
                errmsg = traceback.format_exc()
                logger.error(f"生成微博图片发生错误！错误信息：\n{errmsg}")
                return None
            pass
    pic = modify_pic(pic)
    pic_path = os.path.join(pic_config_dict["pic_save_path"], "weibo", subtype, uid, f"{data['id']}.jpeg")
    save_pic(pic, pic_path)
    content.append('[CQ:image,file=file:///'+pic_path+']')
    content.append(f"微博链接：{'https://m.weibo.cn/detail/' + data['id']}")
    return content

@cmd(("weibo", ))
async def weibo_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: list[str] = []
    if data["user"].get("avatar"):
        if pic_config_dict["weibo_avatar_save"]:
            pic_path = os.path.join(pic_config_dict["pic_save_path"], "weibo", "avatar", f"{uid}.jpeg")
            save_pic(await download_image(data["user"]["avatar"], weibo_headers), pic_path)
            content.append('[CQ:image,file=file:///'+pic_path+']')
        else:
            content.append('[CQ:image,file='+data["user"]["avatar"]+']')
    if("retweet" in data):
        content.append(f"{data['user']['name']}在{data['created_time']}转发了{data['retweet']['user']['name']}的微博并说：\n")
    else:
        content.append(f"{data['user']['name']}在{data['created_time']}发了新微博并说：\n")
    content.append(data['text'] + '\n')
    for i, pic_info in enumerate(data['pics'], 1):
        if pic_config_dict["weibo_pic_save"]:
            pic_path = os.path.join(pic_config_dict["pic_save_path"], "weibo", subtype, uid, data['id'], f"{i}.jpeg")
            save_pic(await download_image(pic_info, weibo_headers), pic_path)
            content.append('[CQ:image,file=file:///'+pic_path+']')
        else:
            content.append('[CQ:image,file='+pic_info+']')
    content.append('\n')
    if("retweet" in data):
        content.append(f"原微博：\n{data['retweet']['text']}\n")
        for i, pic_info in enumerate(data['retweet']['pics'], 1):
            if pic_config_dict["weibo_pic_save"]:
                pic_path = os.path.join(pic_config_dict["pic_save_path"], "weibo", subtype, data['retweet']['user']['uid'], data['retweet']['id'], f"{i}.jpeg")
                save_pic(await download_image(pic_info, weibo_headers), pic_path)
                content.append('[CQ:image,file=file:///'+pic_path+']')
            else:
                content.append('[CQ:image,file='+pic_info+']')
        content.append('\n')
    content.append(f"微博链接：{'https://m.weibo.cn/detail/' + data['id']}")
    return content

@cmd(("comment", ))
async def weibo_comment_builder(subtype: str, uid: str, data: dict):
    content: list[str] = []
    if("reply" in data):
        content.append(f"{data['user']['name']}在{data['created_time']}回复了{data['reply']['user']['name']}的微博评论并说：\n")
    else:
        content.append(f"{data['user']['name']}在{data['created_time']}发了新微博评论并说：\n")
    content.append(data['text'] + '\n')
    for i, pic_info in enumerate(data['pics'], 1):
        if pic_config_dict["weibo_pic_save"]:
            pic_path = os.path.join(pic_config_dict["pic_save_path"], "weibo", subtype, uid, data['id'], f"{i}.jpeg")
            save_pic(await download_image(pic_info, weibo_headers), pic_path)
            content.append('[CQ:image,file=file:///'+pic_path+']')
        else:
            content.append('[CQ:image,file='+pic_info+']')
    content.append('\n')
    if("reply" in data):
        content.append(f"原评论：\n{data['reply']['text']}\n")
        for i, pic_info in enumerate(data['reply']['pics'], i):
            if pic_config_dict["weibo_pic_save"]:
                pic_path = os.path.join(pic_config_dict["pic_save_path"], "weibo", subtype, data['reply']['user']['uid'], data['reply']['id'], f"{i}.jpeg")
                save_pic(await download_image(pic_info, weibo_headers), pic_path)
                content.append('[CQ:image,file=file:///'+pic_path+']')
            else:
                content.append('[CQ:image,file='+pic_info+']')
        content.append('\n')
    content.append(f"原微博链接：{'https://m.weibo.cn/detail/' + data['root']['id']}")
    return content

@cmd(("weibo", ))
async def build_wb_msg(typ: str, subtype: str, uid: str, data: dict):
    data = data_preprocess(data, data["type"])
    builder_list = [
        weibo_pic_builder,
        weibo_builder,
        weibo_comment_builder,
        avatar_builder,
        desc_builder,
        name_builder
    ]
    for builder in builder_list:
        resp = await builder(subtype, uid, data)
        if not resp is None:
            return resp

@cmd(("dynamic", ))
async def dynamic_pic_builder(subtype: str, uid: str, data: dict) -> list[str]:
    if not pic_enable:
        return None
    push_dict = push_pic_config_dict.get(data["type"], {}).get(subtype, {})
    if not (len(data.get("pics", [])) >= pic_config_dict["bili_dyn_pics_limit"] or ("retweet" in data and len(data['retweet'].get("pics", [])) >= pic_config_dict["bili_dyn_pics_limit"])):
        if not (uid in push_dict.get("enable", []) or push_dict.get("enable", "") == "all"):
            return None
    elif uid in push_dict.get("disable", []) or push_dict.get("disable", "") == "all":
        return None

    name = data["user"]["name"]
    content: list[str] = list()
    if not data.get("is_retweet", False):
        content.append(f"{name}在{data['created_time']}")
        if data["dyn_type"] == 8:
            content.append("发了新视频：\n")
        elif data["dyn_type"] == 64:
            content.append("发了新文章：\n")
        elif data["dyn_type"] == 1:
            content.append(f"转发了{data['retweet']['user']['name']}的")
            if data["retweet"]["dyn_type"] == 8:
                content.append("视频：\n")
            elif data["retweet"]["dyn_type"] == 64:
                content.append("文章：\n")
            else:
                content.append("动态：\n")
        else:
            content.append("发了新动态并说：\n")
    for i in range(3):
        try:
            pic = await pic_builder.get_bili_dyn_pic(data["id"], data["created_time"])
            break
        except:
            if i == 2:
                errmsg = traceback.format_exc()
                logger.error(f"生成B站动态图片发生错误！错误信息：\n{errmsg}")
                return None
            pass
    pic = modify_pic(pic)
    pic_path = os.path.join(pic_config_dict["pic_save_path"], "bili_dyn", subtype, uid, f"{data['id']}.jpeg")
    save_pic(pic, pic_path)
    content.append('[CQ:image,file=file:///'+pic_path+']')
    if not data.get("is_retweet", False):
        if data["dyn_type"] == 8:
            content.append("视频链接：\n")
        elif data["dyn_type"] == 64:
            content.append("文章链接：\n")
        else:
            content.append("动态链接：\n")
        content.append(f"{data['link']}")
    return content

@cmd(("dynamic", ))
async def dynamic_builder(subtype: str, uid: str, data: dict) -> list[str]:
    name = data["user"]["name"]
    content: list[str] = list()
    if data["user"].get("avatar"):
        content.append('[CQ:image,file='+data["user"]["avatar"]+']')
    if not data.get("is_retweet", False):
        content.append(f"{name}在{data['created_time']}")
        if data["dyn_type"] == 8:
            content.append("发了新视频：\n")
        elif data["dyn_type"] == 64:
            content.append("发了新文章：\n")
        elif data["dyn_type"] == 1:
            content.append(f"转发了{data['retweet']['user']['name']}的")
            if data["retweet"]["dyn_type"] == 8:
                content.append("视频：\n")
            elif data["retweet"]["dyn_type"] == 64:
                content.append("文章：\n")
            else:
                content.append("动态：\n")
        else:
            content.append("发了新动态并说：\n")
    if data["dyn_type"] == 2 or data["dyn_type"] == 4: # 动态
        content.append(data["text"] + "\n")
        if("pics" in data):
            for pic in data["pics"]:
                content.append('[CQ:image,file='+pic+']')
    elif data["dyn_type"] == 8 or data["dyn_type"] == 64: # 视频 or 文章
        content.append(data["title"] + "\n")
        content.append('[CQ:image,file='+data['cover_pic']+']')
        content.append(data["desc"])
    elif data["dyn_type"] == 1: # 转发
        content.append(data["text"] + "\n")
        content.append("\n" + "原")
        if data["retweet"]["dyn_type"] == 8:
            content.append("视频：\n")
        elif data["retweet"]["dyn_type"] == 64:
            content.append("文章：\n")
        else:
            content.append("动态：\n")
        content.extend(await dynamic_builder(subtype, uid, data["retweet"]))
    else:
        content.append("[无法解析该动态，请点击链接查看]")
    if not data.get("is_retweet", False):
        content.append("\n")
        if data["dyn_type"] == 8:
            content.append("视频链接：\n")
        elif data["dyn_type"] == 64:
            content.append("文章链接：\n")
        else:
            content.append("动态链接：\n")
        content.append(f"{data['link']}")
    return content

@cmd(("comment", ))
async def dynamic_comment_builder(subtype: str, uid: str, data: dict):
    content: list[str] = []
    # content.append('[CQ:image,file='+data["user"]["avatar"]+']')
    if("reply" in data):
        content.append(f"{data['user']['name']}在{data['created_time']}回复了{data['reply']['user']['name']}的动态评论并说：\n")
    else:
        content.append(f"{data['user']['name']}在{data['created_time']}发了新动态评论并说：\n")
    content.append(data['text'] + '\n')
    content.append('\n')
    if("reply" in data):
        content.append(f"原评论：\n{data['reply']['text']}\n")
        content.append('\n')
    content.append(f"原动态链接：{'https://t.bilibili.com/' + data['root']['id']}")
    return content

@cmd(("bili_dyn", ))
async def build_dyn_msg(typ: str, subtype: str, uid: str, data: dict):
    data = data_preprocess(data, data["type"])
    builder_list = [
        dynamic_pic_builder,
        dynamic_builder,
        dynamic_comment_builder,
        avatar_builder,
        desc_builder,
        name_builder
    ]
    for builder in builder_list:
        resp = await builder(subtype, uid, data)
        if not resp is None:
            return resp

@cmd(("status", ))
async def status_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: list[str] = list()
    if(data['now'] == "1"):
        content.append(f"{data['user']['name']}开播啦！")
        content.append(f"标题：\n{data['user']['title']}\n")
        if data['user']['cover']:
            content.append('[CQ:image,file='+data['user']['cover']+']\n')
        content.append(f"链接：https://live.bilibili.com/{data['user']['room_id']}")
    elif(data['pre'] == "1"):
        content.append(f"{data['user']['name']}下播了")
    return content

@cmd(("title",))
async def title_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: list[str] = list()
    content.append(f"{data['user']['name']}更改了直播间标题：\n")
    content.append(data["now"])
    return content

@cmd(("cover",))
async def cover_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: list[str] = list()
    content.append(f"{data['user']['name']}更改了直播间封面：\n")
    content.append('[CQ:image,file='+data['now']+']')
    return content

@cmd(("bili_live", ))
async def build_live_msg(typ: str, subtype: str, uid: str, data: dict):
    data = data_preprocess(data, data["type"])
    builder_list = [
        status_builder,
        title_builder,
        cover_builder
    ]
    for builder in builder_list:
        resp = await builder(subtype, uid, data)
        if not resp is None:
            return resp