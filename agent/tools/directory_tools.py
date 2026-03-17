"""
目录操作工具集
"""

from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from utils.logger import get_logger
from .common import resolve_path

logger = get_logger("agent.tools.directory")


@tool
def list_directory(path: str = ".", pattern: Optional[str] = None, show_hidden: bool = False, workdir: Optional[str] = None) -> str:
    """
    列出目录内容

    Args:
        path: 目录路径（默认当前目录，支持相对路径）
        pattern: 文件模式（如 "*.py"）
        show_hidden: 是否显示隐藏文件
        workdir: 工作目录/项目路径（相对路径会基于此目录）

    Returns:
        目录列表
    """
    dir_path = resolve_path(path, workdir)

    if not dir_path.exists():
        return f"错误：目录不存在 - {path}"

    if not dir_path.is_dir():
        return f"错误：不是目录 - {path}"

    try:
        if pattern:
            files = list(dir_path.glob(pattern))
        else:
            files = list(dir_path.iterdir())

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


@tool
def create_directory(path: str, parents: bool = True, workdir: Optional[str] = None) -> str:
    """
    创建目录

    Args:
        path: 目录路径（支持相对路径）
        parents: 是否创建父目录
        workdir: 工作目录/项目路径（相对路径会基于此目录）

    Returns:
        操作结果
    """
    dir_path = resolve_path(path, workdir)

    if dir_path.exists():
        if dir_path.is_dir():
            return f"提示：目录已存在 - {path}"
        else:
            return f"错误：同名文件已存在 - {path}"

    try:
        dir_path.mkdir(parents=parents, exist_ok=True)
        return f"✅ 已创建目录：{path}"
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def delete_directory(path: str, recursive: bool = False, confirm: bool = False, workdir: Optional[str] = None) -> str:
    """
    删除目录

    Args:
        path: 目录路径（支持相对路径）
        recursive: 是否递归删除
        confirm: 确认删除（必须为 True）
        workdir: 工作目录/项目路径（相对路径会基于此目录）

    Returns:
        操作结果
    """
    dir_path = resolve_path(path, workdir)

    if not dir_path.exists():
        return f"错误：目录不存在 - {path}"

    if not dir_path.is_dir():
        return f"错误：不是目录 - {path}"

    if not confirm:
        return f"警告：删除目录需要 confirm=True 确认 - {path}"

    try:
        if recursive:
            import shutil
            shutil.rmtree(dir_path)
            return f"✅ 已递归删除目录：{path}"
        else:
            dir_path.rmdir()
            return f"✅ 已删除空目录：{path}"
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def move_path(path: str, destination: str, overwrite: bool = False, workdir: Optional[str] = None) -> str:
    """
    移动文件或目录

    Args:
        path: 源路径（支持相对路径）
        destination: 目标路径（支持相对路径）
        overwrite: 是否覆盖目标
        workdir: 工作目录/项目路径（相对路径会基于此目录）

    Returns:
        操作结果
    """
    src = resolve_path(path, workdir)
    dst = resolve_path(destination, workdir)

    if not src.exists():
        return f"错误：源路径不存在 - {path}"

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
        return f"✅ 已移动：{path} → {destination}"
    except Exception as e:
        return f"错误：{str(e)}"


# 工具名称映射（用于显示中文名称）
TOOL_DISPLAY_NAMES = {
    "list_directory": "列出目录内容",
    "create_directory": "创建目录",
    "delete_directory": "删除目录",
    "move_path": "移动文件或目录",
}


def get_directory_tools():
    """获取所有目录操作工具"""
    return [
        list_directory,
        create_directory,
        delete_directory,
        move_path,
    ]
