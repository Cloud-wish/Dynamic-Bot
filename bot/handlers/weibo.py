from __future__ import annotations
import traceback
import json
import copy

from ..utils.logger import get_logger
from ..utils.config import get_config_value
from ..utils.model import Message, MessageType, BotType
from ..utils.msg_queue import put_message
from ..adapters.init import is_adapter_exist
from ..constants.type import type_dict
from ..handlers.init import HandlerTableDef, HandlerNotFoundException
from .utils.msg_preprocess import msg_preprocess

from ..builders.build_push_msg import build_push_msg

from .common import common_push_handler
from .init import get_handler_table

logger = get_logger()
handlers = get_handler_table()

wb_handlers = HandlerTableDef()

@handlers.handler("weibo")
async def dispatch_wb_push(typ: str, msg: dict):
    msg = msg_preprocess(msg, msg["type"])
    try:
        await wb_handlers(msg["subtype"], msg)
    except HandlerNotFoundException:
        logger.error(f"接收到无法解析的{type_dict.get(typ, '未知类型')}消息！消息内容：\n{json.dumps(msg, ensure_ascii=False)}")
    except:
        logger.error(f"解析{type_dict.get(typ, '未知类型')}消息时发生错误！错误消息：\n{traceback.format_exc()}")

@wb_handlers.handler("weibo")
async def wb_handler(subtype: str, data: dict):
    await common_push_handler(subtype, data)

@wb_handlers.handler("comment")
async def wb_cmt_handler(subtype: str, data: dict):
    pass