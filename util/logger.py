import configparser
import logging
import os
from logging.handlers import TimedRotatingFileHandler

logger: logging.Logger = None
LOGGER_NAME = "dynamic-bot"
LOGGER_PRINT_FORMAT = "\033[1;33m[%(levelname)s] (%(filename)s:%(lineno)s) %(funcName)s:\033[0m\n%(message)s"
LOGGER_FILE_FORMAT = "%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)s) %(funcName)s:\n%(message)s"
logging.basicConfig(format=LOGGER_PRINT_FORMAT)

def init_logger(log_path: str) -> logging.Logger:
    global logger
    if(not logger is None):
        return logger
    cf = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=["#"], comment_prefixes=["#"])
    cf.read(f"config.ini", encoding="UTF-8")
    is_debug = cf.getboolean("logger", "debug")
    log_path = os.path.join(log_path, f"{LOGGER_NAME}.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger = logging.getLogger(LOGGER_NAME)
    handler = TimedRotatingFileHandler(log_path, when="midnight", interval=1, encoding="UTF-8")
    handler.setFormatter(logging.Formatter(LOGGER_FILE_FORMAT))
    # 从配置文件接收是否打印debug日志
    if is_debug:
        logger.setLevel(level=logging.DEBUG)
        handler.level = logging.DEBUG
    else:
        logger.setLevel(logging.INFO)
        handler.level = logging.INFO
    logger.addHandler(handler)
    return logger