from __future__ import annotations
import json
import asyncio
import websockets
import traceback

from ..utils.logger import get_logger
from ..utils.config import get_config_value
from ..handlers.init import HandlerNotFoundException
from ..handlers.init import get_handler_table
from .init import get_task_table

from ..constants.type import type_dict
logger = get_logger()
tasks = get_task_table()
handlers = get_handler_table()
                
@tasks.task()
async def receive_push():
    while True: # 断线重连
        try:
            async with websockets.connect(get_config_value("crawler", "ws_url")) as websocket:
                logger.info(f"成功建立与Crawler的Websocket连接")
                msg = {"type": "init", "client_name": get_config_value("crawler", "client_name")} # 初始化Websocket连接
                await websocket.send(json.dumps(msg))
                resp = json.loads(await websocket.recv())
                if(resp["code"] != 0):
                    logger.error(f"与Crawler的Websocket连接返回错误!\ncode:{resp['code']} msg:{resp['msg']}")
                    break

                while True:
                    # 接收消息
                    msg = json.loads(await websocket.recv())
                    logger.debug(f"与Crawler的Websocket连接接收到推送消息, 内容如下:\n{json.dumps(msg, ensure_ascii=False)}")
                    await dispatch_push(msg)
        except Exception as e:
            logger.error(f"与Crawler的Websocket连接出错!错误信息:\n{traceback.format_exc()}\n尝试重连...")
            await asyncio.sleep(1)

async def dispatch_push(msg: dict[str]):
    try:
        typ = msg["type"]
        await handlers(typ, msg)
    except HandlerNotFoundException:
        logger.error(f"接收到无法解析的{type_dict.get(typ, '未知类型')}消息！消息内容：\n{json.dumps(msg, ensure_ascii=False)}")
    except:
        logger.error(f"解析{type_dict.get(typ, '未知类型')}消息时发生错误！错误消息：\n{traceback.format_exc()}")

    # msg_type = msg["type"]
    # subtype = msg["subtype"]
    # uid = msg["user"]["uid"]
    # if not uid:
    #     logger.error(f"接收到无UID的{type_dict.get(msg_type, '未知类型')}消息!消息内容:\n{msg}")
    #     return
    # msg_push_config = get_push_config_value(msg_type)
    # if(msg_push_config):
    #     if(subtype in msg_push_config and type(msg_push_config[subtype]) == dict):
    #         push_channel_list = msg_push_config[subtype].get(uid)
    #     else:
    #         push_channel_list = msg_push_config.get(uid)
    #     if(push_channel_list):
    #         blocked_channel_list = get_push_config_value("blocked")
    #         if blocked_channel_list:
    #             push_channel_list = list(set(push_channel_list) - set(blocked_channel_list))
    #         push_msg_list = await build_notify_msg(msg, push_channel_list)
    #         if(push_msg_list):
    #             logger.info(f"接收到消息:\n{push_msg_list[0]['content']}\n推送频道列表:{push_channel_list}")
    #             for push_msg in push_msg_list:
    #                 await put_message(push_msg)