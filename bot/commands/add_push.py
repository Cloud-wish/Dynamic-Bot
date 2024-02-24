from __future__ import annotations

from ..utils.model import Message
from ..utils import db
from ..constants.command import command_dict
from ..constants.type import type_dict
from ..utils.msg_queue import put_message

from .init import get_command_table
from .utils.get_user_auth import get_user_auth
from .utils.crawler import add_crawler, remove_crawler
commands = get_command_table()

@commands.cmd((command_dict["add"]["weibo"], "weibo", "weibo"), (command_dict["add"]["bili_dyn"], "bili_dyn", "dynamic"), (command_dict["add"]["bili_live"], "bili_live", ("status", "title", "cover")))
async def add_push(cmd: str, typ: str, subtypes: str|tuple[str], msg: Message, uid: str):
    bot_id = msg["bot_id"]
    user = msg["sender"]
    guild_id = msg["guild_id"]
    channel_id = msg["channel_id"]
    if not await get_user_auth(bot_id, guild_id, channel_id, user, typ):
        return None
    if type(subtypes) == str:
        subtypes = (subtypes, )
    
    for _ in [1]:
        if not db.exist_push_user(uid, typ):
            resp = await add_crawler(uid, typ)
            if not resp["success"]:
                if resp and resp["result"]["code"] == 11:
                    reply_content = f"UID：{uid} 未开通直播间"
                else:
                    reply_content = f"UID：{uid} 的{type_dict[typ]}推送添加失败！"
                break
        for subtype in subtypes:
            db.add_push(typ, subtype, uid, bot_id, guild_id, channel_id)
        reply_content = f"UID：{uid} 的{type_dict[typ]}推送添加成功！"

    reply_msg = Message({
      "guild_id": msg["guild_id"],
      "channel_id": msg["channel_id"],
      "msg_type": msg["msg_type"],
      "bot_type": msg["bot_type"],
      "bot_id": msg["bot_id"],
      "data": [{
                "type": "text",
                "data": {
                    "text": reply_content
                }
        }]
    })
    await put_message(reply_msg)
    