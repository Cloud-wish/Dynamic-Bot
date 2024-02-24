import logging
import os
import ruamel.yaml
from logging.handlers import TimedRotatingFileHandler

from .config import CONFIG_PATH, ConfigFileNotFoundError

LOGGER_PRINT_FORMAT = "\033[1;33m%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)s) %(funcName)s:\033[0m\n%(message)s"
LOGGER_FILE_FORMAT = "%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)s) %(funcName)s:\n%(message)s"
logging.basicConfig(format=LOGGER_PRINT_FORMAT)

logger = None
logger_name = None

def get_logger() -> logging.Logger:
    global logger
    if logger is None:
        init_logger()
    return logger

def get_logger_name() -> str:
    global logger_name
    if logger_name is None:
        init_logger()
    return logger_name

def init_logger() -> logging.Logger:
    global logger
    yaml = ruamel.yaml.YAML()
    try:
        with open(CONFIG_PATH, "r", encoding="UTF-8") as f:
            config_dict = yaml.load(f)
    except FileNotFoundError:
        raise ConfigFileNotFoundError
    logger_config = config_dict["logger"]
    is_debug = logger_config["debug"]
    logger_name = logger_config["name"]
    logger_path = os.path.join(os.getcwd(), "logs", f"{logger_name}.log")
    os.makedirs(os.path.dirname(logger_path), exist_ok=True)
    logger = logging.getLogger(logger_name)
    handler = TimedRotatingFileHandler(logger_path, when="midnight", interval=1, encoding="UTF-8")
    handler.setFormatter(logging.Formatter(LOGGER_FILE_FORMAT))
    # 从配置文件接收是否打印debug日志
    if is_debug:
        logger.setLevel(level=logging.DEBUG)
        handler.level = logging.DEBUG
    else:
        logger.setLevel(logging.INFO)
        handler.level = logging.INFO
    logger.addHandler(handler)