from __future__ import annotations
import base64
import traceback
import httpx
import os

from ..utils.logger import get_logger
from ..utils.model import BotType
from ..utils.config import get_config_value
from ..utils.pic_process import modify_pic, save_pic, print_on_pic, compress_pic, download_pic
from ..constants.type import type_dict

from .build_push_msg import BuilderTableDef, get_builder_table, get_pic_builder
from .utils.msg_convert import msg_convert

logger = get_logger()
builders = get_builder_table()

dyn_builders = BuilderTableDef()
dyn_icqq_builders = BuilderTableDef()
dyn_official_builders = BuilderTableDef()

def get_dyn_icqq_builder():
    return dyn_icqq_builders

def get_dyn_official_builder():
    return dyn_official_builders

@builders.builder("bili_dyn")
async def dyn_builder(typ: str, data: dict, bot_id: str, bot_type: BotType) -> dict[str]:
    return await dyn_builders(bot_type, data)

@dyn_builders.builder(BotType.ICQQ)
async def icqq_builder(bot_type: BotType, data: dict) -> dict[str]:
    subtype = data["subtype"]
    return await dyn_icqq_builders(subtype, data)

@dyn_builders.builder(BotType.OFFICIAL)
async def official_builder(bot_type: BotType, data: dict) -> dict[str]:
    raise NotImplementedError("Official bot does not support bili_dyn message")
    # return await dyn_builders(bot_type, data)

@dyn_icqq_builders.builder("dynamic")
async def icqq_dynamic_builder(subtype: str, data: dict) -> dict[str]:
    # 目前实现: 直接返回图片
    # TODO: 设置图片/文字格式
    dyn_content = await dyn_pic_builder(subtype, data, get_config_value("builder", "bili_dyn", "pic_fail_fallback"))
    if get_config_value("builder", "bili_dyn", "link"):
        footer = "\n"
        if data["dyn_type"] == 8:
            footer += "视频地址：\n"
        elif data["dyn_type"] == 64:
            footer += "文章地址：\n"
        else:
            footer += "动态地址：\n"
        footer += f"{data['link']}"
        dyn_content.append({
            "type": "text",
            "data": {"text": footer}
        })
    return dyn_content

async def dyn_pic_builder(subtype: str, data: dict, fallback: bool = False) -> list[dict[str]]:
    # if not pic_enable:
    #     return None

    name = data['user']["name"]
    content: str = ""
    file_image: bytes = None
    # uid = data["user"]["uid"]
    pic_builder = get_pic_builder()
    if not data.get("is_retweet", False):
        content += f"{name}在{data['created_time']}"
        if data["dyn_type"] == 8:
            content += "发了新视频："
        elif data["dyn_type"] == 64:
            content += "发了新文章："
        elif data["dyn_type"] == 1:
            content += f"转发了{data['retweet']['user']['name']}的"
            if data["retweet"]["dyn_type"] == 8:
                content += "视频："
            elif data["retweet"]["dyn_type"] == 64:
                content += "文章："
            else:
                content += "动态："
        else:
            content += "发了新动态并说："
    for i in range(3):
        try:
            pic = await pic_builder.get_bili_dyn_pic(data["id"], data["created_time"], data.get("cookie"))
            file_image = modify_pic(pic)
            file_image = compress_pic(file_image)
            # pic_save_path = os.path.join(os.path.abspath(get_config_value("data", "path")), "pics", "bili_dyn", subtype, uid, f"{data['id']}.jpeg")
            # save_pic(file_image, pic_save_path)
            # content += '[CQ:image,file=file:///'+pic_save_path+']'
            break
        except:
            if i == 2:
                errmsg = traceback.format_exc()
                logger.error(f"生成B站动态图片发生错误！错误信息：\n{errmsg}")
                if fallback: # 回落到文字
                    return await dynamic_builder(subtype, data)
                else:
                    content += "[图片无法生成]"
                    file_image = None
            pass
    return msg_convert(content, file_image)

async def dynamic_builder(subtype: str, data: dict) -> list[str]:
    name = data["user"]["name"]
    content: list[dict[str]] = []
    if data["user"].get("avatar"):
        content.append({
            "type": "image",
            "data": {"file": "base64://" + base64.b64encode(await download_pic(data["user"]["avatar"])).decode('utf-8')}
        })
    if not data.get("is_retweet", False):
        title = f"{name}在{data['created_time']}"
        if data["dyn_type"] == 8:
            title += "发了新视频：\n"
        elif data["dyn_type"] == 64:
            title += "发了新文章：\n"
        elif data["dyn_type"] == 1:
            title += f"转发了{data['retweet']['user']['name']}的"
            if data["retweet"]["dyn_type"] == 8:
                title += "视频：\n"
            elif data["retweet"]["dyn_type"] == 64:
                title += "文章：\n"
            else:
                title += "动态：\n"
        else:
            title += "发了新动态并说：\n"
        content.append({
            "type": "text",
            "data": {"text": title}
        })
    if data["dyn_type"] == 2 or data["dyn_type"] == 4: # 动态
        content.append({
            "type": "text",
            "data": {"text": data["text"] + "\n"}
        })
        if("pics" in data):
            for pic in data["pics"]:
                content.append({
                    "type": "image",
                    "data": {"file": "base64://" + base64.b64encode(await download_pic(pic)).decode('utf-8')}
                })
    elif data["dyn_type"] == 8 or data["dyn_type"] == 64: # 视频 or 文章
        content.append({
            "type": "text",
            "data": {"text": data["title"] + "\n"}
        })
        content.append({
            "type": "image",
            "data": {"file": "base64://" + base64.b64encode(await download_pic(data["cover_pic"])).decode('utf-8')}
        })
        content.append({
            "type": "text",
            "data": {"text": data["desc"]}
        })
    elif data["dyn_type"] == 1: # 转发
        content.append({
            "type": "text",
            "data": {"text": data["text"] + "\n"}
        })
        title = "原"
        if data["retweet"]["dyn_type"] == 8:
            title += "视频：\n"
        elif data["retweet"]["dyn_type"] == 64:
            title += "文章：\n"
        else:
            title += "动态：\n"
        content.append({
            "type": "text",
            "data": {"text": title}
        })
        content.extend(await dynamic_builder(subtype, data["retweet"]))
    else:
        content.append({
            "type": "text",
            "data": {"text": "[无法解析该动态，请点击地址查看]"}
        })
    return content

@dyn_icqq_builders.builder("comment")
async def dynamic_comment_builder(subtype: str, data: dict):
    content: str = ""
    file_image: bytes = None
    # uid = data["user"]["uid"]
    msg_list: list[dict] = []
    pic_builder = get_pic_builder()
    if("reply" in data):
        content += f"{data['user']['name']}在{data['created_time']}回复了{data['reply']['user']['name']}的动态评论并说："
    else:
        content += f"{data['user']['name']}在{data['created_time']}发了新动态评论并说："
    title = content
    content += "\n"
    content += data['text']
    msg_list.append({"type": "text", "content": content})
    content = ""
    if("reply" in data):
        content += f"\n原评论：\n{data['reply']['text']}"
        msg_list.append({"type": "text", "content": content})
    msg_list.append({"type": "text", "content": "原动态："})
    for i in range(3):
        try:
            pic = await pic_builder.get_bili_dyn_pic(data["root"]["id"], data["root"]["created_time"], data.get("cookie"))
            pic = compress_pic(pic)
            msg_list.append({"type": "pic", "content": pic, "para": {"extend_width": True} })
            break
        except:
            if i == 2:
                errmsg = traceback.format_exc()
                logger.error(f"生成B站动态图片发生错误！错误信息：\n{errmsg}")
                msg_list.append({"type": "text", "content": "[图片无法生成]"})
            pass
    file_image = modify_pic(print_on_pic(msg_list))
    # pic_save_path = os.path.join(os.path.abspath(get_config_value("data", "path")), "pics", "bili_dyn", subtype, uid, f"{data['id']}.jpeg")
    # save_pic(file_image, pic_save_path)
    # title += '[CQ:image,file=file:///'+pic_save_path+']'
    return msg_convert(content, file_image)
