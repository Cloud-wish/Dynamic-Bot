from __future__ import annotations
from functools import partial
from typing import Any
import os
import importlib

class HandlerNotFoundException(Exception):
    def __init__(self, msg: str = ""):
        Exception.__init__(self, msg)

class HandlerTableDef():

    def __init__(self) -> None:
        self._route_dict: dict[str] = {}
    
    def handler(self, *handler_def_list):
        """
        参数顺序：定义时参数+调用时参数
        """
        def inner(func):
            for handler_def in handler_def_list:
                typ = handler_def
                self._route_dict[typ] = partial(func, handler_def)
            return func
        return inner

    def __call__(self, typ: str, *args, **kwds) -> Any:
        if not typ in self._route_dict:
            raise HandlerNotFoundException()
        # print(paras)
        return self._route_dict[typ](*args, **kwds)

handlers = HandlerTableDef()

def get_handler_table():
    return handlers

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