from __future__ import annotations
import copy
import httpx
import traceback
import websockets
import json
from functools import partial

from ..utils.logger import get_logger
from ..utils.model import BotType, Message, MessageType, MessageSender
from ..utils.config import get_config_value
from ..commands.init import is_command

from .utils.dispatch_msg import dispatch_msg
from .init import get_adapter_table

logger = get_logger()
adapters = get_adapter_table()

async def receive_icqq_msg(message: dict[str], bot_config: dict[str], bot_id: str):
    # if(config_dict["bot"]["guild_enable"] and message.get('message_type', "") == 'guild' and message.get('sub_type', "") == 'channel'):
    #     # 频道消息
    #     content: str = message['message'].rstrip()
    #     channel: tuple[str] = (str(message['guild_id']), str(message['channel_id']))
    #     bot_uid = config_dict["bot"]["guild_id"]
    if(message.get('message_type', "") == 'group' and message.get('sub_type', "") == 'normal'):
        # 群聊消息
        if message.get('anonymous', None):
            return
        content: str = message['raw_message'].rstrip()
        guild_id = channel_id = str(message['group_id'])
        msg_type = MessageType.GROUP
        if "self" in message:
            bot_uid = str(message["self"]["user_id"])
        elif "self_id" in message: # 适配go-cqhttp
            bot_uid = str(message["self_id"])
        else:
            logger.error(f"群消息中未获取到Bot ID! 消息内容:{json.dumps(message)}")
            return
    else:
        return
    # if(content.startswith(f'[CQ:at,qq={bot_uid}]')):
    #     # 是at bot的消息
    #     content = content.replace(f'[CQ:at,qq={bot_uid}]', '').lstrip()
    if is_command(content):
        user_id = str(message['sender']['user_id'])
        if msg_type == MessageType.GUILD:
            logger.debug(f"bot:{bot_id} 收到来自频道{guild_id}的子频道{channel_id}的{message['sender']['nickname']}的消息：{content}")
        elif msg_type == MessageType.GROUP:
            logger.debug(f"bot:{bot_id} 收到来自群聊{guild_id}的消息：{content}")
        received_msg = Message(
            content=content,
            guild_id=guild_id,
            channel_id=channel_id,
            msg_type=msg_type,
            bot_type=BotType.ICQQ,
            bot_id=bot_id,
            sender=MessageSender(
                user_id=user_id,
                nickname=message['sender']['nickname'],
                raw=message['sender']
            ),
            raw=message
        )
        await dispatch_msg(received_msg)

@adapters.adapter(BotType.ICQQ)
async def icqq_bot_client(bot_config: dict, bot_id: str):
    await websockets.serve(partial(receiver, bot_config=bot_config, bot_id=bot_id), bot_config["websocket"]["host"], bot_config["websocket"]["port"])

async def receiver(websocket, bot_config: dict[str], bot_id: str):
    ws_relay_conn = None
    logger.info(f"bot:{bot_id} 成功建立与icqq的Websocket连接")
    try:
        async for message in websocket:
            if(bot_config["websocket"]["relay"]["enable"]):
                retry_count = bot_config["websocket"]["relay"]["retry_count"]
                relay_url = bot_config["websocket"]["relay"]["url"]
                for i in range(retry_count + 1):
                    try:
                        if(ws_relay_conn is None):
                            ws_relay_conn = await websockets.connect(relay_url)
                            logger.info(f"bot:{bot_id} 成功建立与转发消息接收端的Websocket连接")
                        await ws_relay_conn.send(message)
                        # logger.debug(f"bot:{bot_id} 向转发消息接收端发送了一条消息: {message}")
                        break
                    except Exception as e:
                        logger.error(f"bot:{bot_id} 与转发消息接收端的Websocket连接出错!错误信息:\n{str(e)}")
                        if(i < retry_count):
                            logger.error(f"bot:{bot_id} 尝试第{i + 1}次重新连接转发消息接收端...")
                        else:
                            logger.error(f"bot:{bot_id} 重连次数超过限制, 放弃重连！消息内容: \n{message}")
                        try:
                            await ws_relay_conn.close()
                        except:
                            pass
                        ws_relay_conn = None
            # logger.debug(message)
            data = json.loads(message)
            if(data.get("post_type", "") == "message"):
                await receive_icqq_msg(data, bot_config, bot_id)
    except Exception as e:
        logger.error(f"bot:{bot_id} 与icqq的Websocket连接出错! 错误信息:\n{traceback.format_exc()}")
    finally:
        if(not ws_relay_conn is None):
            await ws_relay_conn.close()

async def icqq_send_group_msg(msg):
    send_msg = {
        "group_id": msg["guild_id"],
        "message": msg["data"]
    }
    if get_config_value("logger", "debug"):
        _send_msg = copy.deepcopy(send_msg)
        for data in _send_msg["message"]:
            if data["type"] == "image":
                data["data"]["file"] = f'size:{len(data["data"]["file"])}'
        logger.debug(f"bot:{msg['bot_id']} 要发送的消息内容：\n{json.dumps(_send_msg, ensure_ascii=False)}")
    if get_config_value("sender", "debug"):
        logger.debug(f"bot:{msg['bot_id']} 已设置debug模式, 消息不会真正发送")
        return
    try:
        http_api = get_config_value("bots", msg["bot_id"], "api")
        timeout = 15 # default
        try:
            timeout = float(get_config_value("sender", "timeout"))
        except:
            logger.info(f"发送消息请求超时时间设置不合法, 使用默认值 (15s)")
            pass
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{http_api}/send_group_msg", json = send_msg, timeout = timeout)
            try:
                resp = resp.json()
                if(resp['retcode'] != 0):
                    logger.error(f"bot:{msg['bot_id']} 群聊{msg['guild_id']}消息发送失败!\ncode:{resp['retcode']} 错误信息:{resp}")
            except json.decoder.JSONDecodeError:
                logger.error(f"bot:{msg['bot_id']} 群聊{msg['guild_id']}消息发送出错!\n错误信息:\n{resp.text}")
            except httpx.ReadTimeout:
                logger.error(f"bot:{msg['bot_id']} 群聊{msg['guild_id']}消息发送超时!")
    except:
        logger.error(f"bot:{msg['bot_id']} 群聊{msg['guild_id']}消息发送出错!\n错误信息:\n{traceback.format_exc()}")
