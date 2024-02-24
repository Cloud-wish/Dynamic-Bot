import traceback

from ...utils.logger import get_logger
from ...utils.model import Message
from ...commands.init import CommandNotFoundException
from ...commands.init import get_command_table

logger = get_logger()
commands = get_command_table()

async def dispatch_msg(msg: Message):
    try:
        # logger.debug(commands._str_route_dict)
        await commands(msg["content"], msg)
    except CommandNotFoundException:
        logger.error(f"收到无对应命令的消息: {msg['content']}")
    except:
        logger.error(f"命令处理出错!错误信息:\n{traceback.format_exc()}")