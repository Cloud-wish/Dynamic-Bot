from __future__ import annotations
import re
from typing import Any
import importlib
import os

class CommandNotFoundException(Exception):
    def __init__(self, msg: str = ""):
        Exception.__init__(self, msg)

class CommandMissingParameterException(Exception):
    def __init__(self, msg: str = ""):
        Exception.__init__(self, msg)

class CommandTableDef():

    def __init__(self) -> None:
        self._str_route_dict: dict[str, dict[str]] = {}
        self._regex_route_dict: dict[str, dict[str]] = {}
    
    def cmd(self, *cmd_def_list):
        """
        向函数传递的参数顺序: cmd(str/re.Match) + 定义时参数 + 调用时参数 + 消息提取参数
        """
        def inner(func):

            def add_cmd_def(cmd_def):
                cmd_pattern = cmd_def[0]
                if type(cmd_pattern) == str:
                    self._str_route_dict[cmd_pattern] = {
                        "func": func,
                        "paras": cmd_def[1:]
                    }
                elif type(cmd_pattern) == re.Pattern:
                    self._regex_route_dict[cmd_pattern.pattern] = {
                        "func": func,
                        "pattern": cmd_pattern,
                        "paras": cmd_def[1:]
                    }

            if type(cmd_def_list[0]) == tuple: # 多个cmd定义
                for cmd_def in cmd_def_list:
                    add_cmd_def(cmd_def)
            else: # 单个cmd定义
                add_cmd_def(cmd_def_list)
            return func
        return inner

    def __call__(self, msg: str, *args, **kwds) -> Any:
        paras = msg.strip().split(" ") # cmd(str) + 消息提取参数
        i = 0
        while(i < len(paras)):
            if paras[i] == "":
                paras.pop(i)
            else:
                i += 1
        cmd_str = paras[0]
        paras = tuple(paras[1:])

        if cmd_str in self._str_route_dict:
            str_route = self._str_route_dict[cmd_str]
            return str_route["func"](cmd_str, *(str_route["paras"] + args + paras), **kwds)
        else:
            for regex_route in self._regex_route_dict.values():
                match_result = regex_route["pattern"].match(cmd_str)
                if match_result and match_result.group(0) == cmd_str: # 与正则表达式完全匹配
                    return regex_route["func"](match_result, *(regex_route["paras"] + args + paras), **kwds)
        raise CommandNotFoundException()
    
    def is_command(self, msg: str) -> bool:
        cmd_str = msg.strip().split(" ")[0]
        if cmd_str in self._str_route_dict:
            return True
        for regex_route in self._regex_route_dict.values():
            match_result = regex_route["pattern"].match(cmd_str)
            if match_result and match_result.group(0) == cmd_str: # 与正则表达式完全匹配
                return True
        return False

commands = CommandTableDef()

def get_command_table():
    return commands

def is_command(msg: str) -> bool:
    return commands.is_command(msg)

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