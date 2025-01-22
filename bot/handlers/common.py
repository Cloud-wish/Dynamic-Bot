from __future__ import annotations
from typing_extensions import Awaitable

from ..utils.logger import get_logger
from ..utils.config import get_config_value
from ..utils.model import MessageType, BotType
from ..utils.msg_queue import put_message
from ..utils.db import get_user_push_config
from ..adapters.init import is_adapter_exist
from ..constants.type import type_dict

from ..builders.build_push_msg import build_push_msg

logger = get_logger()

async def common_push_handler(subtype: str, data: dict, msg_postproc: Awaitable = None):
    typ = data["type"]
    uid = data["user"]["uid"]
    if not uid:
        logger.error(f"接收到无UID的{type_dict.get(typ, '未知类型')}推送消息！消息内容：\n{data}")
        return None
    push_configs = get_user_push_config(typ, subtype, uid)
    push_data_cache = {}
    for push_conf in push_configs:
        bot_id = push_conf["bot_id"]
        bot_conf = get_config_value("bots", bot_id)
        bot_type = BotType(bot_conf["bot_type"])
        if not is_adapter_exist(bot_type):
            logger.error(f"要推送消息的Bot不存在! Bot信息:{bot_conf}")
            continue
        for push_ch in push_conf["channels"]:
            guild_id, channel_id = push_ch[0], push_ch[1]
            if guild_id == channel_id:
                msg_type = MessageType.GROUP
            else:
                msg_type = MessageType.GUILD
            if bot_type in push_data_cache and msg_type in push_data_cache[bot_type]:
                push_data = push_data_cache[bot_type][msg_type]
            else:
                push_data = await build_push_msg(data, bot_id, bot_type)
                if not bot_type in push_data_cache:
                    push_data_cache[bot_type] = {}
                push_data_cache[bot_type][msg_type] = push_data
            push_msg = {
                "bot_id": push_conf["bot_id"],
                "bot_type": bot_type,
                "msg_type": msg_type,
                "data": push_data,
                "guild_id": guild_id,
                "channel_id": channel_id
            }
            if not msg_postproc is None:
                await msg_postproc(push_msg, push_ch, push_conf)
            await put_message(push_msg)