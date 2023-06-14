from __future__ import annotations
import configparser
import copy
import logging
import platform
import os
import json
import requests

logger = logging.getLogger("dynamic-bot")

cf = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=["#"], comment_prefixes=["#"])
cf.read(f"config.ini", encoding="UTF-8")
http_url = cf.get("cqhttp", "http_url")
if http_url.endswith('/'):
    http_url = http_url[0:len(http_url):]
debug_enable = cf.getboolean("sender", "debug")

def send_group_msg(msg: dict):
    send_msg = {
        "group_id": msg["guild_id"],
        "message": "".join(msg["data"])
    }
    if debug_enable:
        logger.debug(f"已开启Debug模式，消息内容：\n{json.dumps(send_msg, ensure_ascii=False)}")
        return
    resp = requests.post(f"{http_url}/send_group_msg", data = send_msg, headers={'Connection':'close'})
    if(resp['retcode'] != 0):
        logger.error(f"消息发送失败，code：{resp['retcode']} 错误信息：{resp['msg']} {resp.get('wording', '')}")