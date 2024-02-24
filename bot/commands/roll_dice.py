from __future__ import annotations
import re
import random

from ..utils.model import Message
from ..utils.msg_queue import put_message
from ..constants.command import command_dict

from .init import get_command_table

commands = get_command_table()

@commands.cmd(re.compile(command_dict["roll"]))
async def roll_dice(cmd: re.Match, msg: Message, roll_content: str = "", *args):
    count = int(cmd.group(1))
    sides = int(cmd.group(2))
    
    if args:
        roll_content += " " + " ".join(args)

    if count < 1 or sides < 1:
        reply_content = "参数错误"
    else:
        result_list: list[int] = []
        sum = 0
        for _ in range(count):
            result = random.randint(1, sides)
            result_list.append(str(result))
            sum += result
        reply_content = f"由于{roll_content}，{msg['sender']['nickname']}投掷: {cmd.group(1)}d{cmd.group(2)}="
        if len(result_list) == 1:
            reply_content += str(sum)
        else:
            reply_content += "{" + "+".join(result_list) + "}=" + str(sum)

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
   