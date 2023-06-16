from __future__ import annotations
import configparser
import random
import re
import time
import jsons
import threading
import queue
import os
import asyncio
import websockets
import logging
import traceback
import httpx

from util.logger import init_logger
from util.bot_command import cmd
from util.send_guild_message import send_guild_msg
from util.send_group_message import send_group_msg
from builder import build_wb_msg, build_dyn_msg, build_live_msg
from constant import command_dict, type_dict, sub_type_dict

log_path = os.path.join(os.path.dirname(__file__), "logs", "bot")
logger: logging.Logger = init_logger(log_path)
msg_queue = queue.Queue(maxsize=-1) # infinity length
config_dict = dict()
push_config_dict = dict()
permission_dict = dict()

BOT_HELP = """1 /添加微博推送
使用方法：@机器人 /添加微博推送 微博UID
2 /添加动态推送
使用方法：@机器人 /添加动态推送 B站UID
3 /添加直播推送
使用方法：@机器人 /添加直播推送 B站UID
4 /删除微博推送
使用方法：@机器人 /删除微博推送 微博UID
5 /删除动态推送
使用方法：@机器人 /删除动态推送 B站UID
6 /删除直播推送
使用方法：@机器人 /删除直播推送 B站UID
7 /关闭推送
使用方法：@机器人 /关闭推送
8 /开启推送
使用方法：@机器人 /开启推送
9 /设置管理员
使用方法：@机器人 /设置管理员 @xxx（在QQ群中可替换为QQ号）
10 /删除管理员
使用方法：@机器人 /删除管理员 @xxx（在QQ群中可替换为QQ号）
11 /查询配置
显示当前子频道的推送配置"""

def cookie_to_dict(cookie: str):
    cookie_list = cookie.split(";")
    cookie_dict = dict()
    for c in cookie_list:
        cookie_pair = c.lstrip().rstrip().split("=")
        cookie_dict[cookie_pair[0]] = cookie_pair[1]
    return cookie_dict

def load_config():
    cf = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=["#"], comment_prefixes=["#"])
    cf.read(f"config.ini", encoding="UTF-8")
    global config_dict, push_config_dict, permission_dict
    for name, section in cf.items():
        config_dict[name] = dict()
        for key, value in section.items():
            try:
                value = int(value)
            except:
                pass
            if(value == "true"):
                value = True
            elif(value == "false"):
                value = False
            config_dict[name][key] = value

    def list_to_set(d: dict):
        for k,v in d.items():
            if type(v) == list:
                d[k] = set([tuple(ch) for ch in v])
            elif type(v) == dict:
                list_to_set(d[k])
        
    try:
        with open("push_config.json", "r", encoding="UTF-8") as f:
            push_config_dict = jsons.loads(f.read())

            if "blocked" in push_config_dict and type(push_config_dict["blocked"]) == list:
                block_list = push_config_dict["blocked"]
                push_config_dict["blocked"] = {
                    "all": block_list
                }
                logger.info("关闭推送的子频道配置迁移完成")

            list_to_set(push_config_dict)
    except:
        pass
    try:
        with open("permission.json", "r", encoding="UTF-8") as f:
            permission_dict = jsons.loads(f.read())

            list_to_set(permission_dict)
    except:
        pass
    # load bot id
    try:
        with httpx.Client() as client:
            if config_dict["bot"]["qq_enable"]:
                resp = client.get(url=config_dict["cqhttp"]["http_url"]+"/get_login_info")
                resp = resp.json()
                if(resp["retcode"] != 0):
                    logger.error(f"获取bot的qq号时返回错误！\ncode：{resp['retcode']} msg：{resp['wording']}")
                    exit(-1)
                config_dict["bot"]["qq_id"] = str(resp["data"]["user_id"])
                logger.info(f'获取到bot的qq号:{config_dict["bot"]["qq_id"]}')
            if config_dict["bot"]["guild_enable"]:
                resp = client.get(url=config_dict["cqhttp"]["http_url"]+"/get_guild_service_profile")
                resp = resp.json()
                if(resp["retcode"] != 0):
                    logger.error(f"获取bot的频道id时返回错误！\ncode：{resp['retcode']} msg：{resp['wording']}")
                    exit(-1)
                config_dict["bot"]["guild_id"] = resp["data"]["tiny_id"]
                logger.info(f'获取到bot的频道id:{config_dict["bot"]["guild_id"]}')
    except:
        errmsg = traceback.format_exc()
        logger.error(f"获取bot id时出错！错误信息：\n{errmsg}")
        exit(-1)

def save_push_config():
    with open("push_config.json", "w", encoding="UTF-8") as f:
        f.write(jsons.dumps(push_config_dict))

def save_permission_config():
    with open("permission.json", "w", encoding="UTF-8") as f:
        f.write(jsons.dumps(permission_dict))

def put_message(guild_id: str, channel_id: str, message: list[str]):
    while(len(message) > 0 and (len(message[-1]) == 0 or message[-1] == "\n")):
        message.pop()
    if(len(message) == 0):
        if guild_id != channel_id:
            logger.error(f"发送至频道{guild_id}的子频道{channel_id}的消息为空！")
        else:
            logger.error(f"发送至群聊{guild_id}的的消息为空！")
        return
    data = {
        "guild_id":guild_id,
        "channel_id":channel_id,
        "data":message
    }
    msg_queue.put(data)

async def add_crawler(uid: str, typ: str, timeout: int = 10, **kwargs) -> bool:
    cmd = {
        "type": typ,
        "uid": uid,
        "client_name": config_dict["bot"]["client_name"]
    }
    for key in kwargs.keys():
        cmd[key] = kwargs[key]
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url=config_dict["crawler"]["http_url"]+"/add", json=cmd, timeout=timeout)
            resp = resp.json()
            if(resp["code"] != 0):
                logger.error(f"向Crawler添加推送时返回错误！\ncode：{resp['code']} msg：{resp['msg']}")
                return {"success":False, "result": resp}
    except:
        errmsg = traceback.format_exc()
        logger.error(f"向Crawler添加推送时出错！错误信息：\n{errmsg}")
        return {"success":False, "result": {"code": -1, "msg": errmsg}}
    return {"success":True, "result": resp}

async def remove_crawler(uid: str, typ: str, subtype: str = None) -> bool:
    cmd = {
        "type": typ,
        "uid": uid,
        "client_name": config_dict["bot"]["client_name"]
    }
    if subtype:
        cmd["subtype"] = subtype
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url=config_dict["crawler"]["http_url"]+"/remove", json=cmd, timeout=10)
            resp = resp.json()
            if(resp["code"] != 0):
                logger.error(f"向Crawler删除推送时返回错误！\ncode：{resp['code']} msg：{resp['msg']}")
                return {"success":False, "result": resp}
    except:
        errmsg = traceback.format_exc()
        logger.error(f"向Crawler删除推送时出错！错误信息：\n{errmsg}")
        return {"success":False, "result": {"code": -1, "msg": errmsg}}
    return {"success":True, "result": resp}

async def get_user_auth(channel: tuple[str, str], user_id: str, typ: str = None, subtype: str = None):
    guild_id = channel[0]
    channel_id = channel[1]
    global permission_dict
    if permission_dict:
        if "root" in permission_dict and user_id in permission_dict["root"]:
            return True
        elif "admin" in permission_dict and guild_id in permission_dict["admin"] and user_id in permission_dict["admin"][guild_id]:
            return True
    try:
        if guild_id != channel_id:
            message = {
                "guild_id":guild_id,
                "user_id":user_id
            }
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{config_dict['cqhttp']['http_url']}/get_guild_member_profile", data = message, headers={'Connection':'close'}, timeout=10)
            user_data = res.json()
            logger.debug(f"频道{channel}用户{user_id}权限查询返回结果:{user_data}")
            if(user_data['retcode'] == 0):
                roles = user_data['data']['roles']
                for role in roles:
                    if(role['role_id'] in ('2', '4')):
                        return True
            else:
                logger.error(f"频道{channel}用户{user_id}权限查询返回错误！\ncode：{user_data['retcode']} msg：{user_data['wording']}")
            return False
        else:
            message = {
                "group_id":guild_id,
                "user_id":user_id
            }
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{config_dict['cqhttp']['http_url']}/get_group_member_info", data = message, headers={'Connection':'close'}, timeout=10)
            user_data = res.json()
            logger.debug(f"群聊{channel[0]}用户{user_id}权限查询返回结果:{user_data}")
            if(user_data['retcode'] == 0):
                role = user_data['data']['role']
                if role in ("owner", "admin"):
                    return True
            else:
                logger.error(f"群聊{channel[0]}用户{user_id}权限查询返回错误！\ncode：{user_data['retcode']} msg：{user_data['wording']}")
            return False
    except:
        errmsg = traceback.format_exc()
        logger.error(f"查询用户权限时出错！错误信息：\n{errmsg}")

@cmd((command_dict["config"]["channel"], ))
async def get_push_config(cmd: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id):
        return None
    if channel[0] != channel[1]:
        channel_type = "子频道"
    else:
        channel_type = "群聊"
    reply = [f"当前{channel_type}中设置的推送如下：\n"]
    for typ in type_dict.keys():
        reply.append(f"{type_dict[typ]}推送：\n")
        if(typ in push_config_dict):
            for x, channels in push_config_dict[typ].items():
                if(type(channels) == dict):
                    continue
                if(channel in channels):
                    reply.append(f"{x}\n")
    for typ in sub_type_dict.keys():
        for subtype in sub_type_dict[typ].keys():
            reply.append(f"{sub_type_dict[typ][subtype]}推送：\n")
            if(typ in push_config_dict and subtype in push_config_dict[typ]):
                for x, channels in push_config_dict[typ][subtype].items():
                    if(channel in channels):
                        reply.append(f"{x}\n")
    reply[-1] = reply[-1].strip()
    return reply

@cmd((command_dict["add"]["weibo"], "weibo"), (command_dict["add"]["bili_dyn"], "bili_dyn"), (command_dict["add"]["bili_live"], "bili_live"))
async def add_push(cmd: str, typ: str, uid: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id, typ):
        return None
    global push_config_dict
    if not typ in push_config_dict:
        push_config_dict[typ] = dict()
    if not uid in push_config_dict[typ]:
        push_config_dict[typ][uid] = set()
    if not channel in push_config_dict[typ][uid]:
        resp = await add_crawler(uid, typ)
        if(resp["success"]):
            push_config_dict[typ][uid].add(channel)
            save_push_config()
            return f"UID：{uid} 的{type_dict[typ]}推送添加成功！"
        else:
            if resp["result"]["code"] == 11:
                return f"UID：{uid} 未开通直播间"
            else: 
                return f"UID：{uid} 的{type_dict[typ]}推送添加失败，请与管理员联系！"
    else:
        return f"UID：{uid} 的{type_dict[typ]}推送已存在！"

@cmd((command_dict["add"]["weibo_comment"], "weibo", "comment"), (command_dict["add"]["bili_dyn_top_comment"], "bili_dyn", "comment"), (command_dict["add"]["bili_dyn_latest_comment"], "bili_dyn", "comment"))
async def add_sub_push(cmd: str, typ: str, subtype: str, uid: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id, typ):
        return None
    global push_config_dict
    if (not typ in push_config_dict) or (not uid in push_config_dict[typ]):
        return f"请先添加UID：{uid} 的{type_dict[typ]}推送！"
    if not subtype in push_config_dict[typ]:
        push_config_dict[typ][subtype] = dict()
    if not uid in push_config_dict[typ][subtype]:
        push_config_dict[typ][subtype][uid] = set()
    if not channel in push_config_dict[typ][subtype][uid]:
        if typ == "bili_dyn" and subtype == "comment":
            is_top = cmd == command_dict["add"]["bili_dyn_top_comment"]
            resp = await add_crawler(uid, typ, 37, subtype = subtype, is_top = is_top)
        else:
            resp = await add_crawler(uid, typ, 37, subtype = subtype)
        if(resp["success"]):
            push_config_dict[typ][subtype][uid].add(channel)
            save_push_config()
            return f"UID：{uid} 的{sub_type_dict[typ][subtype]}推送添加成功！"
        else:
            return f"UID：{uid} 的{sub_type_dict[typ][subtype]}推送添加失败，请与管理员联系！"
    else:
        return f"UID：{uid} 的{sub_type_dict[typ][subtype]}推送已存在！"

@cmd((command_dict["remove"]["weibo"], "weibo"), (command_dict["remove"]["bili_dyn"], "bili_dyn"), (command_dict["remove"]["bili_live"], "bili_live"))
async def remove_push(cmd: str, typ: str, uid: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id, typ):
        return None
    global push_config_dict
    if typ in push_config_dict and uid in push_config_dict[typ] and channel in push_config_dict[typ][uid]:
        if(len(push_config_dict[typ][uid]) == 1):
            resp = await remove_crawler(uid, typ)
            if(resp["success"]):
                del push_config_dict[typ][uid]
                save_push_config()
                return f"UID：{uid} 的{type_dict[typ]}推送删除成功！"
            else:
                return f"UID：{uid} 的{type_dict[typ]}推送删除失败，请与管理员联系！"
        else:
            push_config_dict[typ][uid].remove(channel)
            save_push_config()
            return f"UID：{uid} 的{type_dict[typ]}推送删除成功！"
    else:
        return f"UID：{uid} 的{type_dict[typ]}推送不存在！"

@cmd((command_dict["remove"]["weibo_comment"], "weibo", "comment"), (command_dict["remove"]["bili_dyn_top_comment"], "bili_dyn", "comment"), (command_dict["remove"]["bili_dyn_latest_comment"], "bili_dyn", "comment"))
async def remove_sub_push(cmd: str, typ: str, subtype: str, uid: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id, typ):
        return None
    global push_config_dict
    if typ in push_config_dict and subtype in push_config_dict[typ] and uid in push_config_dict[typ][subtype] and channel in push_config_dict[typ][subtype][uid]:
        if(len(push_config_dict[typ][subtype][uid]) == 1):
            resp = await remove_crawler(uid, typ, subtype)
            if(resp["success"]):
                del push_config_dict[typ][subtype][uid]
                save_push_config()
                return f"UID：{uid} 的{sub_type_dict[typ][subtype]}推送删除成功！"
            else:
                return f"UID：{uid} 的{sub_type_dict[typ][subtype]}推送删除失败，请与管理员联系！"
        else:
            push_config_dict[typ][subtype][uid].remove(channel)
            save_push_config()
            return f"UID：{uid} 的{sub_type_dict[typ][subtype]}推送删除成功！"
    else:
        return f"UID：{uid} 的{sub_type_dict[typ][subtype]}推送不存在！"

def cq_at_replace(matched: re.Match):
    user_id: str = matched.group(1)
    return user_id

@cmd((command_dict["permission"]["grant"], ))
async def grant_user_auth(cmd: str, uid: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id):
        return None
    if channel[0] != channel[1]:
        channel_type = "子频道"
    else:
        channel_type = "群聊"

    if not uid.isdigit():
        uid = re.sub(r"\[CQ:at,qq=(\S+)?\]", cq_at_replace, uid)

    global permission_dict
    if not "admin" in permission_dict:
        permission_dict["admin"] = dict()
    if not channel[0] in permission_dict:
        permission_dict["admin"][channel[0]] = set()
    if not user_id in permission_dict["admin"][channel[0]]:
        permission_dict["admin"][channel[0]].add(uid)
        save_permission_config()
        return f"已授予该用户管理员权限"
    else:
        return f"该用户已经是管理员"

@cmd((command_dict["permission"]["revoke"], ))
async def revoke_user_auth(cmd: str, uid: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id):
        return None
    if channel[0] != channel[1]:
        channel_type = "子频道"
    else:
        channel_type = "群聊"
    
    if not uid.isdigit():
        uid = re.sub(r"\[CQ:at,qq=(\S+)?\]", cq_at_replace, uid)
    
    global permission_dict
    if not "admin" in permission_dict:
        permission_dict["admin"] = dict()
    if not channel[0] in permission_dict:
        permission_dict["admin"][channel[0]] = set()
    if user_id in permission_dict["admin"][channel[0]]:
        permission_dict["admin"][channel[0]].remove(uid)
        save_permission_config()
        return f"已撤销该用户管理员权限"
    else:
        return f"该用户不是管理员"

@cmd((command_dict["at_all"]["enable"], ))
async def enable_at_all(cmd: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id):
        return None
    if channel[0] != channel[1]:
        channel_type = "子频道"
        return "频道暂不支持该功能！"
    else:
        channel_type = "群聊"
    global push_config_dict
    if(not "at_all" in push_config_dict):
        push_config_dict["at_all"] = set()
    if not channel in push_config_dict["at_all"]:
        push_config_dict["at_all"].add(channel)
        save_push_config()
        return f"成功开启当前{channel_type}的全体成员提醒！"
    else:
        return f"当前{channel_type}的全体成员提醒已开启！"

@cmd((command_dict["at_all"]["disable"], ))
async def disable_at_all(cmd: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id):
        return None
    if channel[0] != channel[1]:
        channel_type = "子频道"
        return "频道暂不支持该功能！"
    else:
        channel_type = "群聊"
    global push_config_dict
    if(not "at_all" in push_config_dict):
        push_config_dict["at_all"] = set(())
    if channel in push_config_dict["at_all"]:
        push_config_dict["at_all"].remove(channel)
        save_push_config()
        return f"成功关闭当前{channel_type}的全体成员提醒！"
    else:
        return f"当前{channel_type}的全体成员提醒已关闭！"

@cmd((command_dict["disable"]["all"], "all"), (command_dict["disable"]["weibo"], "weibo"), (command_dict["disable"]["bili_dyn"], "bili_dyn"))
async def disable_push(cmd: str, typ: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id):
        return None
    if channel[0] != channel[1]:
        channel_type = "子频道"
    else:
        channel_type = "群聊"
    global push_config_dict
    if(not "blocked" in push_config_dict):
        push_config_dict["blocked"] = dict()
    if(not typ in push_config_dict["blocked"]):
        push_config_dict["blocked"][typ] = set()
    if not channel in push_config_dict["blocked"][typ]:
        push_config_dict["blocked"][typ].add(channel)
        save_push_config()
        return f"成功关闭当前{channel_type}的{type_dict[typ]}推送！"
    else:
        return f"当前{channel_type}的{type_dict[typ]}推送已关闭！"

@cmd((command_dict["enable"]["all"], "all"), (command_dict["enable"]["weibo"], "weibo"), (command_dict["enable"]["bili_dyn"], "bili_dyn"))
async def enable_push(cmd: str, typ: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id):
        return None
    if channel[0] != channel[1]:
        channel_type = "子频道"
    else:
        channel_type = "群聊"
    global push_config_dict
    if("blocked" in push_config_dict and typ in push_config_dict["blocked"] and channel in push_config_dict["blocked"][typ]):
        push_config_dict["blocked"][typ].remove(channel)
        save_push_config()
        return f"成功开启当前{channel_type}的{type_dict[typ]}推送！"
    else:
        return f"当前{channel_type}的{type_dict[typ]}推送已开启！"

@cmd((command_dict["disable"]["bili_live_start"], "bili_live", "live_start"), (command_dict["disable"]["bili_live_end"], "bili_live", "live_end"), (command_dict["disable"]["bili_live_title"], "bili_live", "title"), (command_dict["disable"]["bili_live_cover"], "bili_live", "cover"))
async def disable_sub_push(cmd: str, typ: str, subtype: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id):
        return None
    if channel[0] != channel[1]:
        channel_type = "子频道"
    else:
        channel_type = "群聊"

    global push_config_dict
    if(not "blocked" in push_config_dict):
        push_config_dict["blocked"] = dict()
    if(not "subtype" in push_config_dict):
        push_config_dict["blocked"]["subtype"] = dict()
    sub_block_config_dict = push_config_dict["blocked"]["subtype"]

    if(not typ in sub_block_config_dict):
        sub_block_config_dict[typ] = dict()
    if(not subtype in sub_block_config_dict):
        sub_block_config_dict[typ][subtype] = set()
    if not channel in sub_block_config_dict[typ][subtype]:
        sub_block_config_dict[typ][subtype].add(channel)
        save_push_config()
        return f"成功关闭当前{channel_type}的{sub_type_dict[typ][subtype]}推送！"
    else:
        return f"当前{channel_type}的{sub_type_dict[typ][subtype]}推送已关闭！"

@cmd((command_dict["enable"]["bili_live_start"], "bili_live", "live_start"), (command_dict["enable"]["bili_live_end"], "bili_live", "live_end"), (command_dict["enable"]["bili_live_title"], "bili_live", "title"), (command_dict["enable"]["bili_live_cover"], "bili_live", "cover"))
async def enable_sub_push(cmd: str, typ: str, subtype: str, user_id: str, channel: tuple[str, str]) -> str:
    if not await get_user_auth(channel, user_id):
        return None
    if channel[0] != channel[1]:
        channel_type = "子频道"
    else:
        channel_type = "群聊"

    global push_config_dict
    if(not "blocked" in push_config_dict):
        push_config_dict["blocked"] = dict()
    if(not "subtype" in push_config_dict):
        push_config_dict["blocked"]["subtype"] = dict()
    sub_block_config_dict = push_config_dict["blocked"]["subtype"]

    if(not typ in sub_block_config_dict):
        sub_block_config_dict[typ] = dict()
    if(not subtype in sub_block_config_dict):
        sub_block_config_dict[typ][subtype] = set()
    if channel in sub_block_config_dict[typ][subtype]:
        sub_block_config_dict[typ][subtype].remove(channel)
        save_push_config()
        return f"成功开启当前{channel_type}的{sub_type_dict[typ][subtype]}推送！"
    else:
        return f"当前{channel_type}的{sub_type_dict[typ][subtype]}推送已开启！"

@cmd((command_dict["help"], ))
async def get_help(cmd: str, user_id: str, channel: tuple[str, str]) -> str:
    return BOT_HELP

async def receiver(websocket):
    global config_dict, ws_relay_conn
    handler_list = [
        get_push_config,
        add_push,
        add_sub_push,
        remove_push,
        remove_sub_push,
        enable_at_all,
        disable_at_all,
        disable_push,
        disable_sub_push,
        enable_push,
        enable_sub_push,
        grant_user_auth,
        revoke_user_auth,
        get_help,
    ]
    ws_relay_conn = None
    logger.info(f"成功建立与cqhttp的Websocket连接")
    try:
        async for message in websocket:
            if(config_dict["cqhttp"]["ws_relay_enable"]):
                for i in range(config_dict["cqhttp"]["ws_relay_reconnect_count"] + 1):
                    try:
                        if(ws_relay_conn is None):
                            ws_relay_conn = await websockets.connect(config_dict["cqhttp"]["ws_relay_url"])
                            logger.info(f"成功建立与转发消息接收端的Websocket连接")
                        await ws_relay_conn.send(message)
                        break
                        # logger.debug(f"向转发消息接收端发送了一条消息：{message}")
                    except Exception as e:
                        logger.error(f"与转发消息接收端的Websocket连接出错！错误信息：\n{str(e)}")
                        if(i < config_dict["cqhttp"]["ws_relay_reconnect_count"]):
                            logger.error(f"尝试第{i + 1}次重新连接转发消息接收端...")
                        else:
                            logger.error(f"重连次数超过限制，放弃重连！消息内容：\n{message}")
                        try:
                            await ws_relay_conn.close()
                        except:
                            pass
                        ws_relay_conn = None
            data = jsons.loads(message)
            if(data.get('post_type', "") == 'message'):
                if(config_dict["bot"]["guild_enable"] and data.get('message_type', "") == 'guild' and data.get('sub_type', "") == 'channel'):
                    # 频道消息
                    content: str = data['message'].rstrip()
                    channel: tuple[str] = (str(data['guild_id']), str(data['channel_id']))
                    bot_id = config_dict["bot"]["guild_id"]
                elif(config_dict["bot"]["qq_enable"] and data.get('message_type', "") == 'group' and data.get('sub_type', "") == 'normal'):
                    # 群聊消息
                    if data.get('anonymous', None):
                        continue
                    content: str = data['raw_message'].rstrip()
                    channel: tuple[str] = (str(data['group_id']), str(data['group_id']))
                    bot_id = config_dict["bot"]["qq_id"]
                else:
                    continue
                if(content.startswith(f'[CQ:at,qq={bot_id}]')):
                    # 是at bot的消息
                    content = content.replace(f'[CQ:at,qq={bot_id}]', '').lstrip()
                    user_id = str(data['sender']['user_id'])
                    logger.debug(f"收到来自频道{channel[0]}的子频道{channel[1]}的{data['sender']['nickname']}的消息：{content}")
                    for handler in handler_list:
                        resp = await handler(content, user_id, channel)
                        if not resp is None:
                            if(type(resp) == str):
                                resp = [resp]
                            put_message(channel[0], channel[1], resp)
                            break
    except Exception as e:
        logger.error(f"与cqhttp的Websocket连接出错！错误信息：\n{traceback.format_exc()}")
    finally:
        if(not ws_relay_conn is None):
            await ws_relay_conn.close()

async def build_notify_msg(data) -> list[str]:
    typ = data["type"]
    subtype = data["subtype"]
    uid = data["user"]["uid"]
    if not uid:
        logger.error(f"接收到无UID的{type_dict.get(typ, '未知类型')}消息！消息内容：\n{data}")
        return None
    builder_list = {
        build_wb_msg,
        build_dyn_msg,
        build_live_msg
    }
    try:
        for builder in builder_list:
            resp = await builder(typ, subtype, uid, data)
            if not resp is None:
                return resp
        logger.error(f"接收到无法解析的{type_dict.get(typ, '未知类型')}消息！消息内容：\n{data}")
    except:
        logger.error(f"解析{type_dict.get(typ, '未知类型')}消息时发生错误！错误消息：\n{traceback.format_exc()}")

def is_channel_blocked(channel: tuple[str,str], msg: dict) -> bool:
    msg_type = msg["type"]
    subtype = msg["subtype"]
    if msg_type == "bili_live" and subtype == "status":
        if(msg['now'] == "1"):
            subtype = "live_start"
        elif(msg['pre'] == "1"):
            subtype = "live_end"
        else:
            logger.error(f"接收到状态未知的直播间消息\n消息内容:{msg}")
            return True
    if "all" in push_config_dict["blocked"] and channel in push_config_dict["blocked"]["all"]:
        return True
    if msg_type in push_config_dict["blocked"] and channel in push_config_dict["blocked"][msg_type]:
        return True
    elif "subtype" in push_config_dict["blocked"] and msg_type in push_config_dict["blocked"]["subtype"] and subtype in push_config_dict["blocked"]["subtype"][msg_type] and channel in push_config_dict["blocked"]["subtype"][msg_type][subtype]:
        return True
    else:
        return False

async def at_all_process(channel: tuple[str,str], msg: dict, notify_msg: list[dict]) -> None:
    if channel[0] != channel[1]:
        logger.error(f"@全体成员推送设置错误，频道暂不支持该功能，请修改")
        return
    msg_type = msg["type"]
    if "at_all" in push_config_dict and channel in push_config_dict["at_all"]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url=config_dict["cqhttp"]["http_url"]+"/get_group_at_all_remain", json={"group_id": channel[0]})
                resp = resp.json()
                if resp["retcode"] != 0:
                    logger.error(f"获取bot在群聊{channel[0]}的@全体成员剩余次数时返回错误！\ncode：{resp['retcode']} msg：{resp['wording']}")
                else:
                    if resp["data"]["can_at_all"] and resp["data"]["remain_at_all_count_for_uin"] > 0:
                        notify_msg.insert(0, "[CQ:at,qq=all]") # 添加@全体成员
                    else:
                        notify_msg.insert(0, "(@全体成员次数已耗尽)")
                        logger.info(f"bot在群聊{channel[0]}的@全体成员剩余次数已耗尽")
        except:
            logger.error(f"处理@全体成员的推送消息时出错!错误信息:{traceback.format_exc()}")

async def dispatcher():
    while True: # 断线重连
        try:
            async with websockets.connect(config_dict["crawler"]["ws_url"]) as websocket:
                logger.info(f"成功建立与Crawler的Websocket连接")
                msg = {"type": "init", "client_name": config_dict["bot"]["client_name"]} # 初始化Websocket连接
                await websocket.send(jsons.dumps(msg))
                resp = jsons.loads(await websocket.recv())
                if(resp["code"] != 0):
                    logger.error(f"与Crawler的Websocket连接返回错误！\ncode：{resp['code']} msg：{resp['msg']}")
                    break
                while True:
                    # 接收消息
                    msg = jsons.loads(await websocket.recv())
                    logger.debug(f"与Crawler的Websocket连接接收到推送消息，内容如下：\n{jsons.dumps(msg, ensure_ascii=False)}")
                    msg_type = msg["type"]
                    subtype = msg["subtype"]
                    uid = msg["user"]["uid"]
                    if not uid:
                        logger.error(f"接收到无UID的{type_dict.get(msg_type, '未知类型')}消息！消息内容：\n{msg}")
                        continue
                    if(msg_type in push_config_dict):
                        push_channel_list = None
                        if(subtype in push_config_dict[msg_type]):
                            if(type(push_config_dict[msg_type][subtype]) == dict):
                                push_channel_list = push_config_dict[msg_type][subtype].get(uid)
                        else:
                            push_channel_list = push_config_dict[msg_type].get(uid)
                        if(push_channel_list):
                            notify_msg = await build_notify_msg(msg)
                            if(notify_msg):
                                logger.info(f"接收到消息：\n{notify_msg}\n推送频道列表：{push_channel_list}")
                                for channel in push_channel_list:
                                    if not is_channel_blocked(channel, msg):
                                        at_all_process(channel, msg, notify_msg)
                                        put_message(channel[0], channel[1], notify_msg)
        except Exception as e:
            logger.error(f"与Crawler的Websocket连接出错！错误信息：\n{traceback.format_exc()}\n尝试重连...")
            await asyncio.sleep(1)

def msg_sender():
    global msg_queue
    while True:
        msg = msg_queue.get(block = True, timeout = None)
        msg_queue.task_done()
        if msg['guild_id'] != msg['channel_id']:
            logger.debug(f"消息发送线程接收到要发送到频道{msg['guild_id']}的子频道{msg['channel_id']}的消息：\n{''.join(msg['data'])}")
            send_guild_msg(msg)
        else:
            logger.debug(f"消息发送线程接收到要发送到群聊{msg['guild_id']}的消息：\n{''.join(msg['data'])}")
            send_group_msg(msg)
        time.sleep(random.random() + 1)

def main():
    load_config()
    sender = threading.Thread(target = msg_sender)
    sender.start()
    asyncio.get_event_loop().run_until_complete(websockets.serve(receiver, config_dict["cqhttp"]["ws_reverse_host"], config_dict["cqhttp"]["ws_reverse_port"]))
    asyncio.get_event_loop().create_task(dispatcher())
    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    main()
    
