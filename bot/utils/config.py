import os
import traceback
import httpx
import ruamel.yaml
import copy
from typing import Any

yaml = ruamel.yaml.YAML()
CONFIG_PATH = os.path.join(os.getcwd(), "config.yaml")
config_dict = None

# TODO 需要加载文件的配置项处理
# 交给调用代码自己加载
file_value_dict = {}

class ConfigKeyError(Exception):
    def __init__(self, msg: str = ""):
        Exception.__init__(self, msg)

class ConfigFileNotFoundError(Exception):
    def __init__(self, msg: str = ""):
        Exception.__init__(self, msg)

class ConfigLoadError(Exception):
    def __init__(self, msg: str = ""):
        Exception.__init__(self, msg)

from .logger import get_logger
logger = get_logger()

def load_config():
    global config_dict
    try:
        with open(CONFIG_PATH, "r", encoding="UTF-8") as f:
            config_dict = yaml.load(f)
    except FileNotFoundError:
        raise ConfigFileNotFoundError

def save_config():
    with open(CONFIG_PATH, "w", encoding="UTF-8") as f:
        yaml.dump(config_dict, f)

def get_config_value(*args) -> Any:
    value = config_dict
    for key in args:
        if not type(value) == ruamel.yaml.CommentedMap:
            raise ConfigKeyError(f"\nkey列表:{args}\n出错的key:{key}\n当前的value:{value}")
        value = value[key]
    if type(value) == dict():
        return copy.deepcopy(value)
    else:
        return value

def set_config_value(value_new: Any, *args) -> Any:
    value = config_dict
    if not args:
        raise ConfigKeyError("需要至少1个key值")
    for key in args[:-1]:
        if not type(value) == ruamel.yaml.CommentedMap:
            raise ConfigKeyError(f"\nkey列表:{args}\n出错的key:{key}\n当前的value:{value}")
        value = value[key]
    value[args[-1]] = value_new

def init_config():
    load_config()