from __future__ import annotations

from ..utils.model import Message
from ..utils import db
from ..constants.command import command_dict
from ..constants.type import type_dict
from ..utils.msg_queue import put_message
from ..utils.model import MessageType

from .init import get_command_table
from .utils.get_user_auth import get_user_auth
commands = get_command_table()

@commands.cmd((command_dict["config"]["channel"], ))
async def get_push_config(cmd: str, msg: Message):
    bot_id = msg["bot_id"]
    user = msg["sender"]
    guild_id = msg["guild_id"]
    channel_id = msg["channel_id"]
    msg_type = msg["msg_type"]
    if not await get_user_auth(bot_id, guild_id, channel_id, user):
        return None

    if msg_type == MessageType.GUILD:
        channel_type = "频道"
    else:
        channel_type = "群聊"
    reply = [f"当前{channel_type}中设置的推送如下：\n"]
    for typ in type_dict.keys():
        reply.append(f"{type_dict[typ]}推送：")
        push_config = db.get_bot_push_config(bot_id, guild_id, channel_id, typ)
        if push_config[typ]:
            reply.append("、".join(push_config[typ]) + "\n")
        else:
            reply.append("无\n")

    reply[-1] = reply[-1].strip()
    reply_msg = Message({
        "guild_id": msg["guild_id"],
        "channel_id": msg["channel_id"],
        "msg_type": msg["msg_type"],
        "bot_type": msg["bot_type"],
        "bot_id": msg["bot_id"],
        "data": [{
                "type": "text",
                "data": {
                    "text": "".join(reply)
                }
        }]
    })
    await put_message(reply_msg)