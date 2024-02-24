from __future__ import annotations
from typing import Any, Coroutine
import importlib
import os

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

class TaskTableDef():

    def __init__(self) -> None:
        self._task_set: set[Coroutine] = set()
    
    def task(self):
        def inner(task_func):
            self._task_set.add(task_func)
            return task_func
        return inner
    
    def add(self, task_func: Coroutine):
        self._task_set.add(task_func)

    def remove(self, task_func: Coroutine):
        self._task_set.remove(task_func)
    
    def get_all_tasks(self) -> list[Coroutine]:
        return list(self._task_set)

tasks = TaskTableDef()

def get_task_table():
    return tasks

def get_all_tasks():
    return tasks.get_all_tasks()

auto_import(os.path.dirname(__file__))

from . import *