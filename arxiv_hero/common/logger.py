from loguru import logger
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_ROOT_DIR = os.path.join(BASE_DIR, ".logs")
os.makedirs(LOG_ROOT_DIR, exist_ok=True)


# 公共日志文件格式（按时间动态分文件夹）
def get_log_path(level_name):
    return os.path.join(LOG_ROOT_DIR, "{time:YYYY-MM-DD}", f"{level_name.lower()}.log")


# 通用 add 函数
def add_logger(level_name):
    logger.add(
        get_log_path(level_name),
        level=level_name,
        rotation="00:00",  # 每天0点新建文件
        retention="30 days",  # 保留30天，自动清理
        encoding="utf-8",
        filter=lambda record: record["level"].name == level_name,
    )


# 添加各级别日志
for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    add_logger(level)
