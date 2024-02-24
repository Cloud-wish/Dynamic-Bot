from __future__ import annotations
import json
import traceback
import httpx
import os

from ...utils.model import MessageSender
from...utils.config import get_config_value
from ...utils.logger import get_logger

logger = get_logger()

async def get_user_auth(bot_id: str, guild_id: str, channel_id: str, user: MessageSender, typ: str = None, subtype: str = None):
    user_id = user["user_id"]
    http_api = get_config_value("bots", bot_id, "api")
    if os.path.exists(os.path.join(get_config_value("data", "path"), "admin.json")):
        with open(os.path.join(get_config_value("data", "path"), "admin.json"), "r", encoding="UTF-8") as f:
            admins = set(json.load(f))
            if user_id in admins:
                return True
    try:
        if guild_id != channel_id:
            message = {
                "guild_id":guild_id,
                "user_id":user_id
            }
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{http_api}/get_guild_member_profile", data = message, headers={'Connection':'close'}, timeout=10)
            user_data = res.json()
            logger.debug(f"频道{guild_id}子频道{channel_id}用户{user_id}权限查询返回结果:{user_data}")
            if(user_data['retcode'] == 0):
                roles = user_data['data']['roles']
                for role in roles:
                    if(role['role_id'] in ('2', '4')):
                        return True
            else:
                logger.error(f"频道{guild_id}子频道{channel_id}用户{user_id}权限查询返回错误！\ncode:{user_data['retcode']} msg:{user_data['wording']}")
            return False
        else:
            message = {
                "group_id":guild_id,
                "user_id":user_id
            }
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{http_api}/get_group_member_info", data = message, headers={'Connection':'close'}, timeout=10)
            user_data = res.json()
            logger.debug(f"群聊{guild_id}用户{user_id}权限查询返回结果:{user_data}")
            if(user_data['retcode'] == 0):
                role = user_data['data']['role']
                if role in ("owner", "admin"):
                    return True
            else:
                logger.error(f"群聊{guild_id}用户{user_id}权限查询返回错误！\ncode:{user_data['retcode']} msg:{user_data['wording']}")
            return False
    except:
        errmsg = traceback.format_exc()
        logger.error(f"查询用户权限时出错! 错误信息:\n{errmsg}")