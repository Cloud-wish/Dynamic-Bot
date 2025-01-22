from __future__ import annotations
import traceback
import httpx
import os

from ..utils.logger import get_logger
from ..utils.model import BotType
from ..utils.config import get_config_value
from ..utils.pic_process import modify_pic, save_pic, print_on_pic, compress_pic, download_pic
from ..constants.type import type_dict

from .build_push_msg import BuilderTableDef, get_builder_table
from .utils.msg_convert import msg_convert

logger = get_logger()
builders = get_builder_table()

live_builders = BuilderTableDef()
live_icqq_builders = BuilderTableDef()
live_official_builders = BuilderTableDef()

@builders.builder("bili_live")
async def live_builder(typ: str, data: dict, bot_id: str, bot_type: BotType) -> dict[str]:
    return await live_builders(bot_type, data)

@live_builders.builder(BotType.ICQQ)
async def icqq_builder(bot_type: BotType, data: dict) -> dict[str]:
    subtype = data["subtype"]
    return await live_icqq_builders(subtype, data)

@live_builders.builder(BotType.OFFICIAL)
async def official_builder(bot_type: BotType, data: dict) -> dict[str]:
    raise NotImplementedError("Official bot does not support bili_live message")
    # return await live_builders(bot_type, data)

@live_icqq_builders.builder("status")
async def status_builder(subtype: str, data: dict) -> list[str]:
    content: str = ""
    file_image: bytes = None
    uid = data["user"]["uid"]
    if(data['now'] == "1"):
        content += f"{data['user']['name']}开播啦！"
        content += f"标题：\n{data['user']['title']}"
        file_image = await download_pic(url=data['user']["cover"])
        # pic_save_path = os.path.join(os.path.abspath(get_config_value("data", "path")), "pics", "bili_live", "cover", f"{uid}_cover.jpeg")
        # save_pic(file_image, pic_save_path)
        # content += '[CQ:image,file=file:///'+pic_save_path+']'
    elif(data['pre'] == "1"):
        content += f"{data['user']['name']}下播了"
    return msg_convert(content, file_image)

@live_icqq_builders.builder("title")
async def title_builder(subtype: str, data: dict) -> list[str]:
    content: str = ""
    content += f"{data['user']['name']}更改了直播间标题：\n"
    content += data["now"]
    return msg_convert(content, None)

@live_icqq_builders.builder("cover")
async def cover_builder(subtype: str, data: dict) -> list[str]:
    content: str = ""
    file_image: bytes = None
    uid = data["user"]["uid"]
    content += f"{data['user']['name']}更改了直播间封面："
    file_image = await download_pic(url=data["now"])
    # pic_save_path = os.path.join(os.path.abspath(get_config_value("data", "path")), "pics", "bili_live", "cover", f"{uid}_cover.jpeg")
    # save_pic(file_image, pic_save_path)
    # content += '[CQ:image,file=file:///'+pic_save_path+']'
    return msg_convert(content, file_image)