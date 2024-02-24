from __future__ import annotations
import re
import random

from ..utils.model import Message
from ..utils.msg_queue import put_message

from ..constants.command import command_dict, HELP

from .init import get_command_table
from .utils.get_user_auth import get_user_auth

commands = get_command_table()

@commands.cmd(command_dict["help"])
async def get_help(cmd: str, msg: Message):
    bot_id = msg["bot_id"]
    user = msg["sender"]
    guild_id = msg["guild_id"]
    channel_id = msg["channel_id"]
    # if not await get_user_auth(bot_id, guild_id, channel_id, user):
    #     return None
    reply_msg = Message({
        "guild_id": msg["guild_id"],
        "channel_id": msg["channel_id"],
        "msg_type": msg["msg_type"],
        "bot_type": msg["bot_type"],
        "bot_id": msg["bot_id"],
        "data": [{
                "type": "text",
                "data": {
                    "text": HELP
                }
        }]
    })
    await put_message(reply_msg)
   