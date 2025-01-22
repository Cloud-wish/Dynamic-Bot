from __future__ import annotations
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

wb_builders = BuilderTableDef()
wb_icqq_builders = BuilderTableDef()
wb_official_builders = BuilderTableDef()

def get_wb_icqq_builder():
    return wb_icqq_builders

def get_wb_official_builder():
    return wb_official_builders

@builders.builder("weibo")
async def wb_builder(typ: str, data: dict, bot_id: str, bot_type: BotType) -> dict[str]:
    return await wb_builders(bot_type, data)

@wb_builders.builder(BotType.ICQQ)
async def icqq_builder(bot_type: BotType, data: dict) -> dict[str]:
    subtype = data["subtype"]
    return await wb_icqq_builders(subtype, data)

@wb_builders.builder(BotType.OFFICIAL)
async def official_builder(bot_type: BotType, data: dict) -> dict[str]:
    raise NotImplementedError("Official bot does not support weibo message")
    # return await wb_builders(bot_type, data)

@wb_icqq_builders.builder("weibo")
async def wb_weibo_builder(subtype: str, data: dict) -> dict[str]:
    # 目前实现: 直接返回图片
    # TODO: 设置图片/文字格式
    return await wb_pic_builder(subtype, data)

async def wb_pic_builder(subtype: str, data: dict) -> list[str]:
    # if not pic_enable:
    #     return None
    content: str = ""
    file_image: bytes = None
    uid = data["user"]["uid"]
    pic_builder = get_pic_builder()
    if("retweet" in data):
        content += f"{data['user']['name']}在{data['created_time']}转发了{data['retweet']['user']['name']}的微博并说："
    else:
        content += f"{data['user']['name']}在{data['created_time']}发了新微博并说："
    for i in range(3):
        try:
            pic = await pic_builder.get_wb_pic(data["id"], data["created_time"], data["cookie"], data["ua"])
            file_image = modify_pic(pic)
            file_image = compress_pic(file_image)
            # pic_save_path = os.path.join(os.path.abspath(get_config_value("data", "path")), "pics", "weibo", subtype, uid, f"{data['id']}.jpeg")
            # save_pic(file_image, pic_save_path)
            # content += '[CQ:image,file=file:///'+pic_save_path+']'
            break
        except:
            if i == 2:
                errmsg = traceback.format_exc()
                logger.error(f"生成微博图片发生错误！错误信息：\n{errmsg}")
                content += "[图片无法生成]"
                file_image = None
            pass
    return msg_convert(content, file_image)

@wb_icqq_builders.builder("comment")
async def wb_cmt_builder(subtype: str, data: dict):
    content: str = ""
    file_image: bytes = None
    uid = data["user"]["uid"]
    pic_builder = get_pic_builder()
    msg_list: list[dict] = []
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "Referer": "https://m.weibo.cn/"
    }
    if("reply" in data):
        content += f"{data['user']['name']}在{data['created_time']}回复了{data['reply']['user']['name']}的微博评论并说："
    else:
        content += f"{data['user']['name']}在{data['created_time']}发了新微博评论并说："
    title = content
    content += "\n"
    content += data['text']
    msg_list.append({"type": "text", "content": content})
    for pic_info in data['pics']:
        msg_list.append({"type": "pic", "content": (await download_pic(pic_info, headers))})
    content = ""
    if("reply" in data):
        content += f"\n原评论：\n{data['reply']['text']}"
        msg_list.append({"type": "text", "content": content})
        for pic_info in data['reply']['pics']:
            msg_list.append({"type": "pic", "content": (await download_pic(pic_info, headers))})
    msg_list.append({"type": "text", "content": "原微博："})
    for i in range(3):
        try:
            pic = await pic_builder.get_wb_pic(data["root"]["id"], data["root"]["created_time"], data["cookie"], data["ua"])
            pic = compress_pic(pic)
            msg_list.append({"type": "pic", "content": pic, "para": {"extend_width": True} })
            break
        except:
            if i == 2:
                errmsg = traceback.format_exc()
                logger.error(f"生成微博图片发生错误！错误信息：\n{errmsg}")
                msg_list.append({"type": "text", "content": "[图片无法生成]"})
            pass
    file_image = modify_pic(print_on_pic(msg_list))
    # pic_save_path = os.path.join(os.path.abspath(get_config_value("data", "path")), "pics", "weibo", subtype, uid, f"{data['id']}.jpeg")
    # save_pic(file_image, pic_save_path)
    # title += '[CQ:image,file=file:///'+pic_save_path+']'
    return msg_convert(content, file_image)