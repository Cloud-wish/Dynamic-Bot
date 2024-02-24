from __future__ import annotations
import copy

from ..utils.pic_process import download_pic
from ..constants.type import type_dict

from .build_push_msg import get_builder_table
from .wb_builder import get_wb_icqq_builder, get_wb_official_builder
from .dyn_builder import get_dyn_icqq_builder, get_dyn_official_builder

builders = get_builder_table()

wb_icqq_builders = get_wb_icqq_builder()
wb_official_builders = get_wb_official_builder()
dyn_icqq_builders = get_dyn_icqq_builder()
dyn_official_builders = get_dyn_official_builder()

_type_dict = copy.deepcopy(type_dict)
_type_dict["bili_dyn"] = "B站"

@wb_icqq_builders.builder("avatar")
@dyn_icqq_builders.builder("avatar")
async def avatar_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: str = ""
    file_image: bytes = None
    content += f"{data['user']['name']}更换了{_type_dict[data['type']]}头像："
    file_image = await download_pic(url=data["now"])
    return {
        "content": content,
        "file_image": file_image
    }

@wb_icqq_builders.builder("desc")
@dyn_icqq_builders.builder("desc")
async def desc_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: str = ""
    file_image: bytes = None
    content += f"{data['user']['name']}更改了{_type_dict[data['type']]}简介：\n"
    content += data["now"]
    return {
        "content": content,
        "file_image": file_image
    }

@wb_icqq_builders.builder("name")
@dyn_icqq_builders.builder("name")
async def name_builder(subtype: str, uid: str, data: dict) -> list[str]:
    content: str = ""
    file_image: bytes = None
    content += f"{data['pre']}更改了{_type_dict[data['type']]}用户名：\n"
    content += data["now"]
    return {
        "content": content,
        "file_image": file_image
    }