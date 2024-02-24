from __future__ import annotations
import asyncio
import traceback
import httpx

from ..utils.model import Message, MessageType, BotType
from ..utils.logger import get_logger
from ..utils.msg_queue import get_msg_queue
from ..utils.config import get_config_value
from .init import get_task_table

# from ..adapters.official_bot_client import official_send_guild_msg
from ..adapters.icqq_bot_client import icqq_send_group_msg

# from botpy.errors import ServerError, AuthenticationFailedError

logger = get_logger()
tasks = get_task_table()

msg_queue = get_msg_queue()

@tasks.task()
async def msg_sender():
    while True:
        try:
            msg: Message = await msg_queue.get()
            msg_queue.task_done()
            if msg["bot_type"] == BotType.ICQQ:
                if msg["msg_type"] == MessageType.GUILD:
                    raise NotImplementedError("暂未实现ICQQ发送频道消息!")
                elif msg["msg_type"] == MessageType.GROUP:
                    await icqq_send_group_msg(msg)
            elif msg["bot_type"] == BotType.OFFICIAL:
                raise NotImplementedError("暂未实现官方Bot发送消息!")
        except:
            logger.error(f"消息发送出错!错误信息:\n{traceback.format_exc()}")