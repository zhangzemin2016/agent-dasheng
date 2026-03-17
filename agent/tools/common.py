"""
工具函数公共模块
提供通用的辅助函数
"""

from pathlib import Path
from typing import Optional


def resolve_path(file_path: str, workdir: Optional[str] = None) -> Path:
    """
    解析文件路径（支持相对路径和绝对路径）

    Args:
        file_path: 文件路径（可以是相对路径或绝对路径）
        workdir: 工作目录（项目路径）

    Returns:
        解析后的 Path 对象
    """
    path = Path(file_path)

    # 如果是绝对路径，直接使用
    if path.is_absolute():
        return path

    # 如果是相对路径且有 workdir，拼接 workdir
    if workdir and not path.is_relative_to(workdir):
        return Path(workdir) / path

    # 否则使用当前目录
    return path
