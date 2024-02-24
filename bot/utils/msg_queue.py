from __future__ import annotations
import asyncio
import json

from .model import Message, MessageType
from .logger import get_logger

logger = get_logger()

msg_queue = asyncio.Queue()

def get_msg_queue():
    return msg_queue

async def put_message(msg: dict):
    if(len(msg["data"]) == 0):
        if msg["msg_type"] == MessageType.GUILD:
            logger.error(f"发送至频道{msg['guild_id']}的子频道{msg['channel_id']}的消息为空！")
        elif msg["msg_type"] == MessageType.GROUP:
            logger.error(f"发送至群聊{msg['guild_id']}的消息为空！")
        return
    if not "bot_id" in msg:
        logger.error(f"消息未指定发送的Bot! 消息内容:{json.dumps(msg, ensure_ascii=False)}")
        return
    await msg_queue.put(msg)