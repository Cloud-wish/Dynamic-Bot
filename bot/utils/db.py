from __future__ import annotations
import os
from .config import get_config_value

from tinydb import TinyDB, where

def init_db():
    os.makedirs(get_config_value("data", "path"), exist_ok=True)
    pass

def add_push(typ: str, subtype: str, uid: str, bot_id: str, guild_id: str, channel_id: str):
    push_db = TinyDB(os.path.join(get_config_value("data", "path"), "push_config.json"))
    try:
        if not push_db.contains(where("bot_id") == bot_id):
            push_config = {
                "bot_id": bot_id
            }
        else:
            push_config = push_db.get(where("bot_id") == bot_id)
        if not typ in push_config:
            push_config[typ] = {}
        if not subtype in push_config[typ]:
            push_config[typ][subtype] = {}
        if not uid in push_config[typ][subtype]:
            push_config[typ][subtype][uid] = []
        push_channels: set[tuple[str]] = set(tuple(ch) for ch in push_config[typ][subtype][uid])
        if not (guild_id, channel_id) in push_channels:
            push_channels.add((guild_id, channel_id))
            push_config[typ][subtype][uid] = list(push_channels)
        push_db.upsert(push_config, where("bot_id") == bot_id)
    except Exception as e:
        raise e
    finally:
        push_db.close()

def remove_push(typ: str, subtype: str, uid: str, bot_id: str, guild_id: str, channel_id: str):
    push_db = TinyDB(os.path.join(get_config_value("data", "path"), "push_config.json"))
    try:
        if not push_db.contains(where("bot_id") == bot_id):
            return
        push_config = push_db.get(where("bot_id") == bot_id)
        if not typ in push_config or \
        not subtype in push_config[typ] or \
        not uid in push_config[typ][subtype]:
            return
        push_channels: set[tuple[str]] = set(tuple(ch) for ch in push_config[typ][subtype][uid])
        if (guild_id, channel_id) in push_channels:
            push_channels.remove((guild_id, channel_id))
            if len(push_channels) == 0:
                del push_config[typ][subtype][uid]
            else:
                push_config[typ][subtype][uid] = list(push_channels)
        push_db.upsert(push_config, where("bot_id") == bot_id)
    except Exception as e:
        raise e
    finally:
        push_db.close()

def exist_push(typ: str, subtype: str, uid: str, bot_id: str, guild_id: str, channel_id: str):
    push_db = TinyDB(os.path.join(get_config_value("data", "path"), "push_config.json"))
    try:
        if not push_db.contains(where("bot_id") == bot_id):
            return False
        push_config = push_db.get(where("bot_id") == bot_id)
        if not typ in push_config or \
           not subtype in push_config[typ] or \
           not uid in push_config[typ][subtype]:
            return False
        push_channels: set[tuple[str]] = set(tuple(ch) for ch in push_config[typ][subtype][uid])
        return (guild_id, channel_id) in push_channels
    except Exception as e:
        raise e
    finally:
        push_db.close()

def exist_push_user(uid: str, typ: str, subtype: str = None):
    push_db = TinyDB(os.path.join(get_config_value("data", "path"), "push_config.json"))
    try:
        push_configs = push_db.all()
        for push_config in push_configs:
            if not typ in push_config:
                continue
            if subtype is None:
                for subtype in push_config[typ].keys():
                    if uid in push_config[typ][subtype]:
                        return True
            else:
                if subtype in push_config[typ] and uid in push_config[typ][subtype]:
                    return True
        return False
    except Exception as e:
        raise e
    finally:
        push_db.close()

def get_user_push_config(typ: str, subtype: str, uid: str):
    results: list[dict[str,list[tuple[str]]]] = []
    push_db = TinyDB(os.path.join(get_config_value("data", "path"), "push_config.json"))
    try:
        push_configs = push_db.all()
        for push_config in push_configs:
            if not typ in push_config or \
            not subtype in push_config[typ] or \
            not uid in push_config[typ][subtype]:
                continue
            results.append({"bot_id": push_config["bot_id"], "channels": [tuple(ch) for ch in push_config[typ][subtype][uid]]})
        return results
    except Exception as e:
        raise e
    finally:
        push_db.close()

def get_bot_push_config(bot_id: str, guild_id: str, channel_id: str, typ: str, subtype: str = None) -> dict[str, dict]:
    push_db = TinyDB(os.path.join(get_config_value("data", "path"), "push_config.json"))
    result: dict[str] = {}
    result[typ] = []
    try:
        if push_db.contains(where("bot_id") == bot_id):
            push_config = push_db.get(where("bot_id") == bot_id)
            if typ in push_config:
                if subtype is None:
                    uids = set()
                    for subtype in push_config[typ].keys():
                        for uid in push_config[typ][subtype].keys():
                            push_channels: set[tuple[str]] = set(tuple(ch) for ch in push_config[typ][subtype][uid])
                            if (guild_id, channel_id) in push_channels:
                                uids.add(uid)
                    result[typ] = list(uids)
                elif subtype in push_config[typ]:
                    result[typ] = {}
                    result[typ][subtype] = []
                    for uid in push_config[typ][subtype].keys():
                        push_channels: set[tuple[str]] = set(tuple(ch) for ch in push_config[typ][subtype][uid])
                        if (guild_id, channel_id) in push_channels:
                            result[typ][subtype].append(uid)
        return result
    except Exception as e:
        raise e
    finally:
        push_db.close()