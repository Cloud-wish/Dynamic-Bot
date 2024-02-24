from __future__ import annotations
import traceback
import json
import os

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

live_handlers = HandlerTableDef()

@handlers.handler("bili_live")
async def dispatch_live_push(typ: str, msg: dict):
    msg = msg_preprocess(msg, msg["type"])
    try:
        await live_handlers(msg["subtype"], msg)
    except HandlerNotFoundException:
        logger.error(f"接收到无法解析的{type_dict.get(typ, '未知类型')}消息！消息内容：\n{json.dumps(msg, ensure_ascii=False)}")
    except:
        logger.error(f"解析{type_dict.get(typ, '未知类型')}消息时发生错误！错误消息：\n{traceback.format_exc()}")

@live_handlers.handler("cover", "title")
async def live_handler(subtype: str, data: dict):
    await common_push_handler(subtype, data)

@live_handlers.handler("status")
async def live_status_handler(subtype: str, data: dict):
    # TODO 替换为统一的db
    async def postproc(push_msg: dict, push_ch: tuple[str], push_conf: dict[str]):
        if data["now"] == "1" and os.path.exists(os.path.join(get_config_value("data", "path"), "at_all_config.json")):
            with open(os.path.join(get_config_value("data", "path"), "at_all_config.json"), "r") as f:
                at_all_config = json.load(f)
                uid = data["user"]["uid"]
                if uid in at_all_config and push_ch in set(tuple(ch) for ch in at_all_config[uid]):
                    push_msg["data"].insert(0, {"type": "text", "data": {"text": "\n"}})
                    push_msg["data"].insert(0, {"type": "at","data": {"qq": "all"}})

    await common_push_handler(subtype, data, msg_postproc=postproc)