"""
目录操作工具集
"""

from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from utils.logger import get_logger

logger = get_logger("agent.tools.directory")


@tool("列出目录内容")
def list_directory(directory: str = ".", pattern: Optional[str] = None, show_hidden: bool = False) -> str:
    """
    列出目录内容

    Args:
        directory: 目录路径（默认当前目录）
        pattern: 文件模式（如 "*.py"）
        show_hidden: 是否显示隐藏文件

    Returns:
        目录列表
    """
    path = Path(directory)

    if not path.exists():
        return f"错误：目录不存在 - {directory}"

    if not path.is_dir():
        return f"错误：不是目录 - {directory}"

    try:
        if pattern:
            files = list(path.glob(pattern))
        else:
            files = list(path.iterdir())

        # 过滤隐藏文件
        if not show_hidden:
            files = [f for f in files if not f.name.startswith('.')]

        result = f"📁 目录：{path.absolute()}\n\n"

        # 分类显示
        dirs = sorted([f for f in files if f.is_dir()])
        files_list = sorted([f for f in files if f.is_file()])

        if dirs:
            result += "目录:\n"
            for d in dirs:
                result += f"  📁 {d.name}/\n"
            result += "\n"

        if files_list:
            result += "文件:\n"
            for f in files_list:
                size = f.stat().st_size
                size_str = f"{size/1024:.1f}K" if size > 1024 else f"{size}B"
                result += f"  📄 {f.name} ({size_str})\n"

        return result or "空目录"

    except Exception as e:
        return f"错误：{str(e)}"


@tool("创建目录")
def create_directory(directory: str, parents: bool = True) -> str:
    """
    创建目录

    Args:
        directory: 目录路径
        parents: 是否创建父目录

    Returns:
        操作结果
    """
    path = Path(directory)

    if path.exists():
        if path.is_dir():
            return f"提示：目录已存在 - {directory}"
        else:
            return f"错误：同名文件已存在 - {directory}"

    try:
        path.mkdir(parents=parents, exist_ok=True)
        return f"✅ 已创建目录：{directory}"
    except Exception as e:
        return f"错误：{str(e)}"


@tool("删除目录")
def delete_directory(directory: str, recursive: bool = False, confirm: bool = False) -> str:
    """
    删除目录

    Args:
        directory: 目录路径
        recursive: 是否递归删除
        confirm: 确认删除（必须为 True）

    Returns:
        操作结果
    """
    path = Path(directory)

    if not path.exists():
        return f"错误：目录不存在 - {directory}"

    if not path.is_dir():
        return f"错误：不是目录 - {directory}"

    if not confirm:
        return f"警告：删除目录需要 confirm=True 确认 - {directory}"

    try:
        if recursive:
            import shutil
            shutil.rmtree(path)
            return f"✅ 已递归删除目录：{directory}"
        else:
            path.rmdir()
            return f"✅ 已删除空目录：{directory}"
    except Exception as e:
        return f"错误：{str(e)}"


@tool("移动文件或目录")
def move_path(source: str, destination: str, overwrite: bool = False) -> str:
    """
    移动文件或目录

    Args:
        source: 源路径
        destination: 目标路径
        overwrite: 是否覆盖目标

    Returns:
        操作结果
    """
    src = Path(source)
    dst = Path(destination)

    if not src.exists():
        return f"错误：源路径不存在 - {source}"

    if dst.exists() and not overwrite:
        return f"错误：目标已存在，设置 overwrite=True 覆盖 - {destination}"

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)

        if overwrite and dst.exists():
            if dst.is_dir():
                import shutil
                shutil.rmtree(dst)
            else:
                dst.unlink()

        src.rename(dst)
        return f"✅ 已移动：{source} → {destination}"
    except Exception as e:
        return f"错误：{str(e)}"


def get_directory_tools():
    """获取所有目录操作工具"""
    return [
        list_directory,
        create_directory,
        delete_directory,
        move_path,
    ]
