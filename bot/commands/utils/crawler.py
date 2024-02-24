from __future__ import annotations
import traceback
import httpx

from...utils.config import get_config_value
from ...utils.logger import get_logger

logger = get_logger()


async def add_crawler(uid: str, typ: str, timeout: int = 10, **kwargs) -> bool:
    cmd = {
        "type": typ,
        "uid": uid,
        "client_name": get_config_value("crawler", "client_name")
    }
    for key in kwargs.keys():
        cmd[key] = kwargs[key]
    try:
        http_api = get_config_value("crawler", "http_url")
        async with httpx.AsyncClient() as client:
            resp = await client.post(url=http_api+"/add", json=cmd, timeout=timeout)
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
        "client_name": get_config_value("crawler", "client_name")
    }
    if subtype:
        cmd["subtype"] = subtype
    try:
        http_api = get_config_value("crawler", "http_url")
        async with httpx.AsyncClient() as client:
            resp = await client.post(url=http_api+"/remove", json=cmd, timeout=10)
            resp = resp.json()
            if(resp["code"] != 0):
                logger.error(f"向Crawler删除推送时返回错误！\ncode：{resp['code']} msg：{resp['msg']}")
                return {"success":False, "result": resp}
    except:
        errmsg = traceback.format_exc()
        logger.error(f"向Crawler删除推送时出错！错误信息：\n{errmsg}")
        return {"success":False, "result": {"code": -1, "msg": errmsg}}
    return {"success":True, "result": resp}