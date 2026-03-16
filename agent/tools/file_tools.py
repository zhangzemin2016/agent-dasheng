"""
文件操作工具集
"""

from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from utils.logger import get_logger

logger = get_logger("agent.tools.file")


@tool("读取文件")
def read_file(file_path: str, max_chars: int = 2000, encoding: str = 'utf-8') -> str:
    """
    读取文件内容

    Args:
        file_path: 文件路径
        max_chars: 最大字符数（默认 2000）
        encoding: 文件编码（默认 utf-8）

    Returns:
        文件内容
    """
    path = Path(file_path)

    if not path.exists():
        return f"错误：文件不存在 - {file_path}"

    if not path.is_file():
        return f"错误：不是文件 - {file_path}"

    try:
        content = path.read_text(encoding=encoding)

        if len(content) > max_chars:
            content = content[:max_chars] + \
                "\n\n...（内容已截断，总长度：{} 字符）".format(len(content))

        return f"📄 文件：{file_path}\n\n{content}"

    except UnicodeDecodeError:
        return f"错误：无法读取文件（编码问题，尝试指定 encoding 参数）- {file_path}"
    except Exception as e:
        return f"错误：{str(e)}"


@tool("写入文件")
def write_file(file_path: str, content: str, overwrite: bool = False, encoding: str = 'utf-8') -> str:
    """
    写入文件

    Args:
        file_path: 文件路径
        content: 文件内容
        overwrite: 是否覆盖已存在的文件
        encoding: 文件编码

    Returns:
        操作结果
    """
    path = Path(file_path)

    if path.exists() and not overwrite:
        return f"错误：文件已存在，设置 overwrite=True 覆盖 - {file_path}"

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return f"✅ 已写入：{file_path} ({len(content)} 字符)"
    except Exception as e:
        return f"错误：{str(e)}"


@tool("编辑文件")
def edit_file(file_path: str, old_text: str, new_text: str, encoding: str = 'utf-8') -> str:
    """
    编辑文件（文本替换）

    Args:
        file_path: 文件路径
        old_text: 要替换的原文本
        new_text: 新的文本
        encoding: 文件编码

    Returns:
        操作结果
    """
    path = Path(file_path)

    if not path.exists():
        return f"错误：文件不存在 - {file_path}"

    try:
        content = path.read_text(encoding=encoding)

        if old_text not in content:
            return f"错误：未找到要替换的文本"

        new_content = content.replace(old_text, new_text)
        path.write_text(new_content, encoding=encoding)

        changes = new_content.count(new_text)
        return f"✅ 已编辑：{file_path} (替换 {changes} 处)"
    except Exception as e:
        return f"错误：{str(e)}"


@tool("删除文件")
def delete_file(file_path: str, confirm: bool = False) -> str:
    """
    删除文件（安全删除）

    Args:
        file_path: 文件路径
        confirm: 确认删除（必须为 True）

    Returns:
        操作结果
    """
    path = Path(file_path)

    if not path.exists():
        return f"错误：文件不存在 - {file_path}"

    if not path.is_file():
        return f"错误：不是文件 - {file_path}"

    if not confirm:
        return f"警告：删除文件需要 confirm=True 确认 - {file_path}"

    try:
        path.unlink()
        return f"✅ 已删除：{file_path}"
    except Exception as e:
        return f"错误：{str(e)}"


@tool("复制文件")
def copy_file(source: str, destination: str, overwrite: bool = False) -> str:
    """
    复制文件

    Args:
        source: 源文件路径
        destination: 目标文件路径
        overwrite: 是否覆盖目标文件

    Returns:
        操作结果
    """
    src = Path(source)
    dst = Path(destination)

    if not src.exists():
        return f"错误：源文件不存在 - {source}"

    if dst.exists() and not overwrite:
        return f"错误：目标文件已存在，设置 overwrite=True 覆盖 - {destination}"

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        return f"✅ 已复制：{source} → {destination}"
    except Exception as e:
        return f"错误：{str(e)}"


def get_file_tools():
    """获取所有文件操作工具"""
    return [
        read_file,
        write_file,
        edit_file,
        delete_file,
        copy_file,
    ]
