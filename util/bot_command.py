from __future__ import annotations
import logging

logger = logging.getLogger("dynamic-bot")

def cmd(*cmd_list):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            msg = args[0] + " "
            for cmd in cmd_list:
                cmd_str = cmd[0]
                typs = cmd[1:len(cmd)]
                if msg.startswith(cmd_str + " "):
                    paras = msg.replace(cmd_str, "").strip().split(" ")
                    if(paras[0] == ""):
                        paras = tuple()
                    else:
                        paras = tuple(paras)
                    para_num = func.__code__.co_argcount - (len(typs) + len(args))
                    # print(cmd_str, typs, paras, para_num)
                    if(len(paras) != para_num):
                        logger.info(f"{func.__name__} 收到指令：{cmd_str}，类型：{typs}，参数个数错误，应为{para_num}，传入参数：{paras}")
                        return "参数个数错误！"
                    else:
                        logger.info(f"{func.__name__} 收到指令：{cmd_str}，类型：{typs}，传入参数：{paras}")
                        args = args[1:len(args)]
                        # print(typs, paras, args)
                        return await func(cmd_str, *(typs+paras+args))
                logger.debug(f"{func.__name__} 指令未找到，原始消息：{msg}，指令：{cmd_str}")
            return None
        return wrapper
    return decorator

if __name__ == "__main__":
    import asyncio
    @cmd(("/test1", "testtyp", "testsubtyp"))
    async def test1(cmd: str, typ: str, subtyp: str, para1: str, para2: str, ch: str, a: int):
        print(cmd, typ, subtyp, para1, para2, ch, a)
        return True
    @cmd(("/test2", ))
    async def test2(cmd: str):
        print(cmd)
        return True
    res = asyncio.run(test1("/test1 abc def", "testch", 1))
    print(res)
    res = asyncio.run(test2("/test2"))
    print(res)