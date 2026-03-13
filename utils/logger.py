"""
日志配置模块
统一配置项目日志，支持文件日志和轮转
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

from constants.builtin_paths import BuiltinPaths


def setup_logger(
    name: str = "ai_agent",
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    log_to_file: bool = True,
    log_dir: str = "",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    配置并返回日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别
        format_string: 自定义格式字符串
        log_to_file: 是否写入文件
        log_dir: 日志目录路径
        max_bytes: 单个日志文件最大字节数
        backup_count: 备份文件数量

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 默认格式
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（带轮转）
    if log_to_file:
        try:
            if not log_dir:
                # 使用应用根目录下的 logs 文件夹
                log_dir = BuiltinPaths.LOG_ROOT

            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)

            log_file = log_path / f"{name}.log"

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            logger.info(f"日志已初始化：{log_file}")
        except Exception as e:
            logger.error(f"初始化文件日志失败：{e}")

    return logger


# 全局日志记录器
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    return logging.getLogger(f"ai_agent.{name}")


def set_log_level(level: int):
    """设置全局日志级别"""
    logging.getLogger("ai_agent").setLevel(level)
    for handler in logging.getLogger("ai_agent").handlers:
        handler.setLevel(level)
