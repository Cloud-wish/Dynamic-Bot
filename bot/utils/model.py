from __future__ import annotations
from typing import TypedDict
from enum import Enum

class MessageType(str, Enum):
    GUILD = "guild"
    GROUP = "group"

class BotType(str, Enum):
    OFFICIAL = "official"
    ICQQ = "icqq"

class Message(TypedDict):
    content: str
    guild_id: str
    channel_id: str
    msg_type: MessageType
    bot_type: BotType
    bot_id: str
    sender: MessageSender
    raw: dict[str]

class MessageSender(TypedDict):
    user_id: str
    nickname: str
    raw: dict[str]