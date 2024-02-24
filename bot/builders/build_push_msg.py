from __future__ import annotations
from functools import partial
from typing import Any
import os
import importlib
from datetime import datetime, timezone, timedelta

from ..utils.model import BotType

from .pic_builder import PicBuilder

class BuilderNotFoundException(Exception):
    def __init__(self, msg: str = ""):
        Exception.__init__(self, msg)

class BuilderTableDef():

    def __init__(self) -> None:
        self._route_dict: dict[str] = {}
    
    def builder(self, *builder_def_list):
        """
        参数顺序：定义时参数+调用时参数
        """
        def inner(func):
            for builder_def in builder_def_list:
                typ = builder_def
                self._route_dict[typ] = partial(func, builder_def)
            return func
        return inner

    def __call__(self, typ: str, *args, **kwds) -> Any:
        if not typ in self._route_dict:
            raise BuilderNotFoundException()
        # print(paras)
        return self._route_dict[typ](*args, **kwds)

builders = BuilderTableDef()
_pic_builder = PicBuilder()

def get_builder_table():
    return builders

def get_pic_builder():
    return _pic_builder

def data_preprocess(data: dict, typ: str) -> dict:
    if("created_time" in data and type(data["created_time"]) == int):
        data["created_time"] = datetime.fromtimestamp(data["created_time"], tz=timezone(timedelta(hours=+8))).strftime("%Y-%m-%d %H:%M:%S")
    if "user" in data and not "name" in data["user"]:
        data["user"]["name"] = "[未知用户名]"
    if("retweet" in data):
        data["retweet"] = data_preprocess(data["retweet"], typ)
    if("reply" in data):
        data["reply"] = data_preprocess(data["reply"], typ)
    return data

async def build_push_msg(data:dict[str], bot_type: BotType) -> dict[str]:
    data = data_preprocess(data, data["type"])
    typ = data["type"]
    subtype = data["subtype"]
    uid = data["user"]["uid"]
    return await builders(typ, bot_type, data)

def auto_import(directory_path):
    """
    导入指定目录下的所有 .py 文件

    :param directory_path: 目录路径
    """
    # 获取指定目录中的所有文件
    file_list = os.listdir(directory_path)

    # 遍历目录中的所有文件
    for filename in file_list:
        if filename.endswith('.py') and filename != '__init__.py' and filename != 'init.py':
            module_name = filename[:-3]  # 去除文件扩展名
            importlib.import_module("." + module_name, __package__)

auto_import(os.path.dirname(__file__))

from . import *