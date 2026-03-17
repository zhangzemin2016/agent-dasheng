"""
文件操作工具集
"""

from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from utils.logger import get_logger
from .common import resolve_path

logger = get_logger("agent.tools.file")


@tool
def read_file(path: str, max_chars: int = 2000, encoding: str = 'utf-8', workdir: Optional[str] = None) -> str:
    """
    读取文件内容

    Args:
        path: 文件路径（支持相对路径）
        max_chars: 最大字符数（默认 2000）
        encoding: 文件编码（默认 utf-8）
        workdir: 工作目录/项目路径（相对路径会基于此目录）

    Returns:
        文件内容
    """
    file_path = resolve_path(path, workdir)

    if not file_path.exists():
        return f"错误：文件不存在 - {path}"

    if not file_path.is_file():
        return f"错误：不是文件 - {path}"

    try:
        content = file_path.read_text(encoding=encoding)

        if len(content) > max_chars:
            content = content[:max_chars] + \
                "\n\n...（内容已截断，总长度：{} 字符）".format(len(content))

        return f"📄 文件：{path}\n\n{content}"

    except UnicodeDecodeError:
        return f"错误：无法读取文件（编码问题，尝试指定 encoding 参数）- {path}"
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def write_file(path: str, content: str, overwrite: bool = False, encoding: str = 'utf-8', workdir: Optional[str] = None) -> str:
    """
    写入文件

    Args:
        path: 文件路径（支持相对路径）
        content: 文件内容
        overwrite: 是否覆盖已存在的文件
        encoding: 文件编码
        workdir: 工作目录/项目路径（相对路径会基于此目录）

    Returns:
        操作结果
    """
    file_path = resolve_path(path, workdir)

    if file_path.exists() and not overwrite:
        return f"错误：文件已存在，设置 overwrite=True 覆盖 - {path}"

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding=encoding)
        return f"✅ 已写入：{path} ({len(content)} 字符)"
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def edit_file(path: str, old_text: str, new_text: str, encoding: str = 'utf-8', workdir: Optional[str] = None) -> str:
    """
    编辑文件（文本替换）

    Args:
        path: 文件路径（支持相对路径）
        old_text: 要替换的原文本
        new_text: 新的文本
        encoding: 文件编码
        workdir: 工作目录/项目路径（相对路径会基于此目录）

    Returns:
        操作结果
    """
    file_path = resolve_path(path, workdir)

    if not file_path.exists():
        return f"错误：文件不存在 - {path}"

    try:
        content = file_path.read_text(encoding=encoding)

        if old_text not in content:
            return f"错误：未找到要替换的文本"

        new_content = content.replace(old_text, new_text)
        file_path.write_text(new_content, encoding=encoding)

        changes = new_content.count(new_text)
        return f"✅ 已编辑：{path} (替换 {changes} 处)"
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def delete_file(path: str, confirm: bool = False, workdir: Optional[str] = None) -> str:
    """
    删除文件（安全删除）

    Args:
        path: 文件路径（支持相对路径）
        confirm: 确认删除（必须为 True）
        workdir: 工作目录/项目路径（相对路径会基于此目录）

    Returns:
        操作结果
    """
    file_path = resolve_path(path, workdir)

    if not file_path.exists():
        return f"错误：文件不存在 - {path}"

    if not file_path.is_file():
        return f"错误：不是文件 - {path}"

    if not confirm:
        return f"警告：删除文件需要 confirm=True 确认 - {path}"

    try:
        file_path.unlink()
        return f"✅ 已删除：{path}"
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def copy_file(path: str, destination: str, overwrite: bool = False, workdir: Optional[str] = None) -> str:
    """
    复制文件

    Args:
        path: 源文件路径（支持相对路径）
        destination: 目标文件路径（支持相对路径）
        overwrite: 是否覆盖目标文件
        workdir: 工作目录/项目路径（相对路径会基于此目录）

    Returns:
        操作结果
    """
    src = resolve_path(path, workdir)
    dst = resolve_path(destination, workdir)

    if not src.exists():
        return f"错误：源文件不存在 - {path}"

    if dst.exists() and not overwrite:
        return f"错误：目标文件已存在，设置 overwrite=True 覆盖 - {destination}"

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        return f"✅ 已复制：{path} → {destination}"
    except Exception as e:
        return f"错误：{str(e)}"


# 工具名称映射（用于显示中文名称）
TOOL_DISPLAY_NAMES = {
    "read_file": "读取文件",
    "write_file": "写入文件",
    "edit_file": "编辑文件",
    "delete_file": "删除文件",
    "copy_file": "复制文件",
}


def get_file_tools():
    """获取所有文件操作工具"""
    return [
        read_file,
        write_file,
        edit_file,
        delete_file,
        copy_file,
    ]
