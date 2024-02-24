from __future__ import annotations
import asyncio

from bot.utils.config import init_config, get_config_value
init_config()

from bot.utils.db import init_db
from bot.utils.model import BotType
from bot.tasks.init import get_all_tasks
from bot.adapters.init import get_adapter, get_adapter_table
from bot.utils.logger import get_logger

logger = get_logger()

def main():
    init_db()
    async_tasks = [task() for task in get_all_tasks()]
    bots = get_config_value("bots")

    logger.debug("adapter list:"+repr(get_adapter_table()._adapter_dict))

    for bot_id, bot_conf in bots.items():
        bot_type = BotType(bot_conf["bot_type"])
        bot_adapter = get_adapter(bot_type)
        if bot_adapter is None:
            logger.error(f"未找到适配器: {bot_type}")
            continue
        async_tasks.append(bot_adapter(bot_conf, bot_id))
    try:
        asyncio.get_event_loop().run_until_complete(asyncio.gather(
            *async_tasks
        ))
    except KeyboardInterrupt:
        logger.info("收到键盘中断, Bot退出")
        exit(0)

if __name__ == '__main__':
    main()