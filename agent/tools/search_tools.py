"""
搜索工具集
"""

import re
from pathlib import Path
from typing import Optional, List

from langchain_core.tools import tool

from utils.logger import get_logger

logger = get_logger("agent.tools.search")


@tool("搜索文件")
def search_files(pattern: str, directory: str = ".", max_results: int = 50) -> str:
    """
    搜索文件（支持 glob 模式）

    Args:
        pattern: 文件模式（如 "**/*.py"）
        directory: 搜索目录（默认当前目录）
        max_results: 最大结果数

    Returns:
        匹配的文件列表
    """
    path = Path(directory)

    if not path.exists():
        return f"错误：目录不存在 - {directory}"

    try:
        files = list(path.rglob(pattern))

        # 排除隐藏目录和常见忽略目录
        exclude_dirs = {'.git', '__pycache__', 'node_modules',
                        '.venv', 'venv', '.idea', '.vscode'}
        files = [f for f in files if not any(
            d in str(f) for d in exclude_dirs)]

        if not files:
            return f"🔍 未找到匹配的文件：{pattern}"

        # 限制结果数
        truncated = len(files) > max_results
        files = files[:max_results]

        result = f"🔍 找到 {len(files)}{'+' if truncated else ''} 个文件:\n\n"
        for f in files:
            rel_path = f.relative_to(path)
            size = f.stat().st_size
            size_str = f"{size/1024:.1f}K" if size > 1024 else f"{size}B"
            result += f"📄 {rel_path} ({size_str})\n"

        if truncated:
            result += f"\n... 还有 {len(files) - max_results} 个文件未显示"

        return result

    except Exception as e:
        return f"错误：{str(e)}"


@tool
def search_content(pattern: str, directory: str = ".", file_pattern: str = "*", max_results: int = 20, use_regex: bool = False) -> str:
    """
    搜索文件内容（类似 grep）

    Args:
        pattern: 搜索模式
        directory: 搜索目录
        file_pattern: 文件模式（如 "*.py"）
        max_results: 最大结果数
        use_regex: 是否使用正则表达式

    Returns:
        匹配结果
    """
    path = Path(directory)

    if not path.exists():
        return f"错误：目录不存在 - {directory}"

    try:
        matches = []

        for file in path.rglob(file_pattern):
            if file.is_file() and '.git' not in str(file):
                try:
                    content = file.read_text(encoding='utf-8')
                    lines = content.split('\n')

                    for i, line in enumerate(lines, 1):
                        if use_regex:
                            if re.search(pattern, line, re.IGNORECASE):
                                matches.append((file, i, line.strip()))
                        else:
                            if pattern.lower() in line.lower():
                                matches.append((file, i, line.strip()))

                        if len(matches) >= max_results * 2:  # 多搜一些用于过滤
                            break
                except:
                    continue

        if not matches:
            return f"🔍 未找到匹配的内容：{pattern}"

        # 限制结果数
        truncated = len(matches) > max_results
        matches = matches[:max_results]

        result = f"🔍 找到 {len(matches)}{'+' if truncated else ''} 处匹配:\n\n"
        for file, line_num, line_content in matches:
            rel_path = file.relative_to(path)
            # 截断过长的行
            if len(line_content) > 200:
                line_content = line_content[:200] + "..."
            result += f"{rel_path}:{line_num}: {line_content}\n"

        if truncated:
            result += f"\n... 还有 {len(matches) - max_results} 处匹配未显示"

        return result

    except Exception as e:
        return f"错误：{str(e)}"


@tool
def find_in_files(pattern: str, files: List[str], use_regex: bool = False) -> str:
    """
    在指定文件中搜索内容

    Args:
        pattern: 搜索模式
        files: 文件路径列表
        use_regex: 是否使用正则表达式

    Returns:
        匹配结果
    """
    matches = []

    for file_path in files:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            continue

        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                if use_regex:
                    if re.search(pattern, line, re.IGNORECASE):
                        matches.append((path, i, line.strip()))
                else:
                    if pattern.lower() in line.lower():
                        matches.append((path, i, line.strip()))
        except:
            continue

    if not matches:
        return f"🔍 未找到匹配的内容：{pattern}"

    result = f"🔍 找到 {len(matches)} 处匹配:\n\n"
    for file, line_num, line_content in matches:
        if len(line_content) > 200:
            line_content = line_content[:200] + "..."
        result += f"{file.name}:{line_num}: {line_content}\n"

    return result


def get_search_tools():
    """获取所有搜索工具"""
    return [
        search_files,
        search_content,
        find_in_files,
    ]
