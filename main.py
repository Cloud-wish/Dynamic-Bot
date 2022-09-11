from __future__ import annotations
import configparser
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
from builder import build_wb_msg, build_dyn_msg, build_live_msg
from constant import command_dict, type_dict

log_path = os.path.join(os.path.dirname(__file__), "logs", "bot")
logger: logging.Logger = init_logger(log_path)
msg_queue = queue.Queue(maxsize=-1) # infinity length
config_dict = dict()
push_config_dict = dict()

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
9 /查询配置
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
    global config_dict, push_config_dict
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
    config_dict["bot"]["bot_id"] = str(config_dict["bot"]["bot_id"])
    try:
        with open("push_config.json", "r", encoding="UTF-8") as f:
            push_config_dict = jsons.loads(f.read())
            for typ in push_config_dict.keys():
                if(type(push_config_dict[typ]) == dict):
                    for uid in push_config_dict[typ].keys():
                        if(type(push_config_dict[typ][uid]) == dict):
                            for subtype in push_config_dict[typ][uid].keys():
                                push_config_dict[typ][uid][subtype] = set([tuple(channel) for channel in push_config_dict[typ][uid][subtype]])
                        else:
                            push_config_dict[typ][uid] = set([tuple(channel) for channel in push_config_dict[typ][uid]])
                else:
                    push_config_dict[typ] = set([tuple(channel) for channel in push_config_dict[typ]])
    except:
        pass

def save_push_config():
    with open("push_config.json", "w", encoding="UTF-8") as f:
        f.write(jsons.dumps(push_config_dict))

def put_guild_channel_msg(guild_id: str, channel_id: str, message: list[str]):
    while(len(message) > 0 and (len(message[-1]) == 0 or message[-1] == "\n")):
        message.pop()
    if(len(message) == 0):
        logger.error(f"发送至频道{guild_id}的子频道{channel_id}的消息为空！")
        return
    data = {
        "guild_id":guild_id,
        "channel_id":channel_id,
        "data":message
    }
    msg_queue.put(data)

async def add_crawler(typ: str, uid: str) -> bool:
    cmd = {
        "type": typ,
        "uid": uid,
        "client_name": config_dict["bot"]["client_name"]
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url=config_dict["crawler"]["http_url"]+"/add", json=cmd, timeout=5)
            resp = resp.json()
            if(resp["code"] != 0):
                logger.error(f"向Crawler添加推送时返回错误！\ncode：{resp['code']} msg：{resp['msg']}")
                return False
    except:
        errmsg = traceback.format_exc()
        logger.error(f"向Crawler添加推送时出错！错误信息：\n{errmsg}")
        return False
    return True

async def remove_crawler(typ: str, uid: str) -> bool:
    cmd = {
        "type": typ,
        "uid": uid,
        "client_name": config_dict["bot"]["client_name"]
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url=config_dict["crawler"]["http_url"]+"/remove", json=cmd, timeout=5)
            resp = resp.json()
            if(resp["code"] != 0):
                logger.error(f"向Crawler删除推送时返回错误！\ncode：{resp['code']} msg：{resp['msg']}")
                return False
    except:
        errmsg = traceback.format_exc()
        logger.error(f"向Crawler删除推送时出错！错误信息：\n{errmsg}")
        return False
    return True

async def get_user_auth(guild_id, user_id):
    message = {
        "guild_id":guild_id,
        "user_id":user_id
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{config_dict['cqhttp']['http_url']}/get_guild_member_profile", data = message, headers={'Connection':'close'}, timeout=10)
    user_data = res.json()
    if(user_data['retcode'] == 0):
        roles = user_data['data']['roles']
        for role in roles:
            if(role['role_id'] == '2'):
                return True
    return False

@cmd((command_dict["add"]["weibo"], "weibo"), (command_dict["add"]["bili_dyn"], "bili_dyn"), (command_dict["add"]["bili_live"], "bili_live"))
async def add_push(cmd: str, typ: str, uid: str, user_id: str, channel: tuple[str, str]) -> str:
    global push_config_dict
    if not typ in push_config_dict:
        push_config_dict[typ] = dict()
    if not uid in push_config_dict[typ]:
        push_config_dict[typ][uid] = set()
    if not channel in push_config_dict[typ][uid]:
        resp = await add_crawler(typ, uid)
        if(resp):
            push_config_dict[typ][uid].add(channel)
            save_push_config()
            return f"UID：{uid} 的{type_dict[typ]}推送添加成功！"
        else:
            return f"UID：{uid} 的{type_dict[typ]}推送添加失败，请与管理员联系！"
    else:
        return f"UID：{uid} 的{type_dict[typ]}推送已存在！"

@cmd((command_dict["remove"]["weibo"], "weibo"), (command_dict["remove"]["bili_dyn"], "bili_dyn"), (command_dict["remove"]["bili_live"], "bili_live"))
async def remove_push(cmd: str, typ: str, uid: str, user_id: str, channel: tuple[str, str]) -> str:
    global push_config_dict
    if typ in push_config_dict and uid in push_config_dict[typ] and channel in push_config_dict[typ][uid]:
        if(len(push_config_dict[typ][uid]) == 1):
            resp = await remove_crawler(typ, uid)
            if(resp):
                del push_config_dict[typ][uid]
                save_push_config()
                return f"UID：{uid} 的{type_dict[typ]}推送删除成功！"
            else:
                return f"UID：{uid} 的{type_dict[typ]}推送删除失败，请与管理员联系！"
        else:
            push_config_dict[typ][uid].remove(uid)
            save_push_config()
            return f"UID：{uid} 的{type_dict[typ]}推送删除成功！"
    else:
        return f"UID：{uid} 的{type_dict[typ]}推送不存在！"

@cmd((command_dict["config"]["channel"], ))
async def get_push_config(cmd: str, user_id: str, channel: tuple[str, str]) -> str:
    reply = ["当前子频道开启的推送如下：\n"]
    for typ in type_dict.keys():
        reply.append(f"{type_dict[typ]}推送：\n")
        if(typ in push_config_dict):
            for uid, channels in push_config_dict[typ].items():
                if(channel in channels):
                    reply.append(f"{uid}\n")
    reply[-1] = reply[-1].strip()
    return reply

@cmd((command_dict["disable"]["channel"], ))
async def disable_push(cmd: str, user_id: str, channel: tuple[str, str]) -> str:
    global push_config_dict
    if(not "blocked" in push_config_dict):
        push_config_dict["blocked"] = set()
    if(not channel in push_config_dict["blocked"]):
        push_config_dict["blocked"].add(channel)
        return "成功关闭当前子频道的推送功能！"
    else:
        return "当前子频道的推送功能已关闭！"

@cmd((command_dict["enable"]["channel"], ))
async def enable_push(cmd: str, user_id: str, channel: tuple[str, str]) -> str:
    global push_config_dict
    if("blocked" in push_config_dict and channel in push_config_dict["blocked"]):
        push_config_dict["blocked"].remove(channel)
        return "成功开启当前子频道的推送功能！"
    else:
        return "当前子频道的推送功能已开启！"

@cmd((command_dict["help"], ))
async def get_help(cmd: str, user_id: str, channel: tuple[str, str]) -> str:
    return BOT_HELP

async def receiver(websocket):
    global config_dict, ws_relay_conn
    bot_id = config_dict["bot"]["bot_id"]
    handler_list = [
        get_push_config,
        add_push,
        remove_push,
        get_help,
        disable_push,
        enable_push
    ]
    ws_relay_conn = None
    logger.error(f"成功建立与cqhttp的Websocket连接")
    try:
        async for message in websocket:
            if(config_dict["cqhttp"]["ws_relay_enable"]):
                for i in range(config_dict["cqhttp"]["ws_relay_reconnect_count"] + 1):
                    try:
                        if(ws_relay_conn is None):
                            ws_relay_conn = websockets.connect(config_dict["cqhttp"]["ws_relay_url"])
                            logger.info(f"成功建立与转发消息接收端的Websocket连接")
                        await ws_relay_conn.send(message)
                        logger.debug(f"向转发消息接收端发送了一条消息：{message}")
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
            if(data.get('post_type', "") == 'message' and data.get('message_type', "") == 'guild' and data.get('sub_type', "") == 'channel'):
                # 频道消息
                content: str = data['message'].rstrip()
                if(content.startswith(f'[CQ:at,qq={bot_id}]')):
                    # 是at bot的消息
                    content = content.replace(f'[CQ:at,qq={bot_id}]', '').lstrip()
                    channel: tuple[str] = (str(data['guild_id']), str(data['channel_id']))
                    user_id = str(data['sender']['user_id'])
                    logger.debug(f"收到来自频道{channel[0]}的子频道{channel[1]}的{data['sender']['nickname']}的消息：{content}")
                    for handler in handler_list:
                        resp = await handler(content, user_id, channel)
                        if not resp is None:
                            if(type(resp) == str):
                                resp = [resp]
                            put_guild_channel_msg(channel[0], channel[1], resp)
                            break
    except Exception as e:
        logger.error(f"与cqhttp的Websocket连接出错！错误信息：\n{traceback.format_exc()}")
    finally:
        if(not ws_relay_conn is None):
            await ws_relay_conn.close()

async def build_notify_msg(data) -> list[str]:
    typ = data["type"]
    subtype = data["subtype"]
    uid = data["uid"]
    builder_list = {
        build_wb_msg,
        build_dyn_msg,
        build_live_msg
    }
    for builder in builder_list:
        resp = await builder(typ, subtype, uid, data)
        if not resp is None:
            return resp
    logger.error(f"接收到无法解析的{type_dict.get(typ, '未知类型')}消息！消息内容：\n{jsons.dumps(data, ensure_ascii=False)}")

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
                    uid = msg["uid"]
                    if(msg_type in push_config_dict and uid in push_config_dict[msg_type] and push_config_dict[msg_type][uid]):
                        if(type(push_config_dict[msg_type][uid]) == dict):
                            push_channel_list = push_config_dict[msg_type][uid][subtype]
                        else:
                            push_channel_list = push_config_dict[msg_type][uid]
                        if(push_channel_list):
                            notify_msg = await build_notify_msg(msg)
                            if(notify_msg):
                                logger.info(f"接收到消息：\n{notify_msg}\n推送频道列表：{push_channel_list}")
                                for channel in push_channel_list:
                                    if(not channel in push_config_dict.get("blocked", tuple())):
                                        put_guild_channel_msg(channel[0], channel[1], notify_msg)
        except Exception as e:
            logger.error(f"与Crawler的Websocket连接出错！错误信息：\n{traceback.format_exc()}\n尝试重连...")

def msg_sender():
    global msg_queue
    while True:
        msg = msg_queue.get(block = True, timeout = None)
        msg_queue.task_done()
        logger.debug(f"消息发送线程接收到要发送到频道{msg['guild_id']}的子频道{msg['channel_id']}的消息：\n{''.join(msg['data'])}")
        send_guild_msg(msg)

def main():
    load_config()
    sender = threading.Thread(target = msg_sender)
    sender.start()
    asyncio.get_event_loop().run_until_complete(websockets.serve(receiver, config_dict["cqhttp"]["ws_reverse_host"], config_dict["cqhttp"]["ws_reverse_port"]))
    asyncio.get_event_loop().create_task(dispatcher())
    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    main()
    
