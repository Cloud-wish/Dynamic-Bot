from __future__ import annotations
from typing import Any, Coroutine
import importlib
import os

from ..utils.model import BotType

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

class AdapterTableDef():

    def __init__(self) -> None:
        self._adapter_dict: dict[BotType, Coroutine] = dict()
    
    def adapter(self, adapter_name: BotType):
        def inner(adapter_func):
            self._adapter_dict[adapter_name] = adapter_func
            return adapter_func
        return inner
    
    def add(self, adapter_name: BotType, adapter_func: Coroutine):
        self._adapter_dict[adapter_name] = adapter_func

    def remove(self, adapter_name: BotType):
        del self._adapter_dict[adapter_name]
    
    def get_all_adapters(self) -> list[Coroutine]:
        return list(self._adapter_dict.values())
    
    def get_adapter(self, adapter_name: BotType) -> Coroutine | None:
        return self._adapter_dict.get(adapter_name)
    
    def is_adapter_exist(self, adapter_name: BotType) -> bool:
        return adapter_name in self._adapter_dict

adapters = AdapterTableDef()

def get_adapter_table():
    return adapters

def get_adapter(adapter_name: BotType):
    return adapters.get_adapter(adapter_name)

def is_adapter_exist(adapter_name: BotType):
    return adapters.is_adapter_exist(adapter_name)

auto_import(os.path.dirname(__file__))

from . import *