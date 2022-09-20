from __future__ import annotations
from datetime import datetime, timedelta, timezone
import logging
import json
from util.bot_command import cmd
from constant import type_dict

logger = logging.getLogger("dynamic-bot")

uid_to_name_dict = None

try:
    with open("uid_to_name.json", "r", encoding="UTF-8") as f:
        uid_to_name_dict = json.loads(f.read())
except:
    pass

def data_preprocess(data: dict, typ: str) -> dict:
    global uid_to_name_dict
    if("created_time" in data):
        data["created_time"] = datetime.fromtimestamp(data["created_time"], tz=timezone(timedelta(hours=+8))).strftime("%Y-%m-%d %H:%M:%S")
    if uid_to_name_dict and "name" in data and typ in uid_to_name_dict and data["uid"] in uid_to_name_dict[typ]:
        data["name"] = uid_to_name_dict[typ][data["uid"]]
    if("retweet" in data):
        data["retweet"] = data_preprocess(data["retweet"], typ)
    if("reply" in data):
        data["reply"] = data_preprocess(data["reply"], typ)
    return data

@cmd(("avatar", ))
async def avatar_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: list[str] = []
    content.append(f"{data['name']}更换了{type_dict[data['type']]}头像：\n")
    content.append('[CQ:image,file='+data["now"]+']')
    return content

@cmd(("desc", ))
async def desc_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: list[str] = []
    content.append(f"{data['name']}更改了{type_dict[data['type']]}简介：\n")
    content.append(data["now"])
    return content

@cmd(("name", ))
async def name_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: list[str] = []
    content.append(f"{data['pre']}更改了{type_dict[data['type']]}用户名：")
    content.append(data["now"])
    return content

@cmd(("weibo", ))
async def weibo_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: list[str] = []
    content.append('[CQ:image,file='+data["avatar"]+']')
    if("retweet" in data):
        content.append(f"{data['name']}在{data['created_time']}转发了{data['retweet']['name']}的微博并说：\n")
    else:
        content.append(f"{data['name']}在{data['created_time']}发了新微博并说：\n")
    content.append(data['text'] + '\n')
    for pic_info in data['pics']:
        content.append('[CQ:image,file='+pic_info+']')
    content.append('\n')
    if("retweet" in data):
        content.append(f"原微博：\n{data['retweet']['text']}\n")
        for pic_info in data['retweet']['pics']:
            content.append('[CQ:image,file='+pic_info+']')
        content.append('\n')
    content.append(f"本条微博地址：{'https://m.weibo.cn/detail/' + data['id']}")
    return content

@cmd(("comment", ))
async def weibo_comment_builder(subtype: str, uid: str, data: dict):
    content: list[str] = []
    content.append('[CQ:image,file='+data["avatar"]+']')
    if("reply" in data):
        content.append(f"{data['name']}在{data['created_time']}回复了{data['reply']['name']}的微博评论并说：\n")
    else:
        content.append(f"{data['name']}在{data['created_time']}发了新微博评论并说：\n")
    content.append(data['text'] + '\n')
    for pic_info in data['pics']:
        content.append('[CQ:image,file='+pic_info+']')
    content.append('\n')
    if("reply" in data):
        content.append(f"原评论：\n{data['reply']['text']}\n")
        for pic_info in data['reply']['pics']:
            content.append('[CQ:image,file='+pic_info+']')
        content.append('\n')
    content.append(f"原微博地址：{'https://m.weibo.cn/detail/' + data['orig_weibo_id']}")
    return content

@cmd(("weibo", ))
async def build_wb_msg(typ: str, subtype: str, uid: str, data: dict):
    data = data_preprocess(data, data["type"])
    builder_list = [
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
async def dynamic_builder(subtype: str, uid: str, data: dict) -> list[str]:
    name = data["name"]
    content: list[str] = list()
    if not data.get("is_retweet", False):
        content.append(f"{name}在{data['created_time']}")
        if data["dyn_type"] == 8:
            content.append("发了新视频：\n")
        elif data["dyn_type"] == 64:
            content.append("发了新文章：\n")
        elif data["dyn_type"] == 1:
            content.append(f"转发了{data['retweet']['name']}的")
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
        content.append(f"{data['link_prefix']}{data['id']}")
    return content

@cmd(("comment", ))
async def dynamic_comment_builder(subtype: str, uid: str, data: dict):
    content: list[str] = []
    content.append('[CQ:image,file='+data["avatar"]+']')
    if("reply" in data):
        content.append(f"{data['name']}在{data['created_time']}回复了{data['reply']['name']}的动态评论并说：\n")
    else:
        content.append(f"{data['name']}在{data['created_time']}发了新动态评论并说：\n")
    content.append(data['text'] + '\n')
    content.append('\n')
    if("reply" in data):
        content.append(f"原评论：\n{data['reply']['text']}\n")
        content.append('\n')
    content.append(f"原动态地址：{'https://t.bilibili.com/' + data['orig_dyn_id']}")
    return content

@cmd(("bili_dyn", ))
async def build_dyn_msg(typ: str, subtype: str, uid: str, data: dict):
    data = data_preprocess(data, data["type"])
    builder_list = [
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
        content.append(f"{data['name']}开播啦！\n")
        content.append(f"直播间标题：\n{data['title']}\n")
        content.append(f"链接：https://live.bilibili.com/{data['room_id']}")
    elif(data['pre'] == "1"):
        content.append(f"{data['name']}下播了")
    return content

@cmd(("title",))
async def title_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: list[str] = list()
    content.append(f"{data['name']}更改了直播间标题：\n")
    content.append(data["now"])
    return content

@cmd(("bili_live", ))
async def build_live_msg(typ: str, subtype: str, uid: str, data: dict):
    data = data_preprocess(data, data["type"])
    builder_list = [
        status_builder,
        title_builder,
    ]
    for builder in builder_list:
        resp = await builder(subtype, uid, data)
        if not resp is None:
            return resp
