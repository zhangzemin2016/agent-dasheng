"""
Dasheng Agent 工具集
基于 LangChain 的 tool 装饰器定义
"""

import subprocess
import re
from pathlib import Path
from typing import Optional, List

from langchain_core.tools import tool

from utils.logger import get_logger

logger = get_logger("agent.tools")


@tool
def read_file(file_path: str, max_chars: int = 2000) -> str:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        max_chars: 最大字符数（默认 2000）
        
    Returns:
        文件内容
    """
    path = Path(file_path)
    
    if not path.exists():
        return f"错误：文件不存在 - {file_path}"
    
    if not path.is_file():
        return f"错误：不是文件 - {file_path}"
    
    try:
        content = path.read_text(encoding='utf-8')
        
        # 截断过长的内容
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n...（内容已截断）"
        
        return f"文件：{file_path}\n\n{content}"
    
    except UnicodeDecodeError:
        return f"错误：无法读取文件（可能是二进制文件）- {file_path}"
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def write_file(file_path: str, content: str, overwrite: bool = False) -> str:
    """
    写入文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        操作结果
    """
    path = Path(file_path)
    
    # 检查文件是否已存在
    if path.exists() and not overwrite:
        return f"错误：文件已存在，设置 overwrite=True 覆盖 - {file_path}"
    
    # 创建父目录
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        path.write_text(content, encoding='utf-8')
        return f"成功：已写入文件 - {file_path} ({len(content)} 字符)"
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def edit_file(file_path: str, old_text: str, new_text: str) -> str:
    """
    编辑文件（替换文本）
    
    Args:
        file_path: 文件路径
        old_text: 要替换的原文本
        new_text: 新的文本
        
    Returns:
        操作结果
    """
    path = Path(file_path)
    
    if not path.exists():
        return f"错误：文件不存在 - {file_path}"
    
    try:
        content = path.read_text(encoding='utf-8')
        
        if old_text not in content:
            return f"错误：未找到要替换的文本"
        
        new_content = content.replace(old_text, new_text)
        path.write_text(new_content, encoding='utf-8')
        
        return f"成功：已编辑文件 - {file_path}"
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def list_directory(directory: str = ".", pattern: Optional[str] = None) -> str:
    """
    列出目录内容
    
    Args:
        directory: 目录路径（默认当前目录）
        pattern: 文件模式（如 "*.py"）
        
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
        
        # 排除隐藏文件和目录
        files = [f for f in files if not f.name.startswith('.')]
        
        result = f"目录：{path.absolute()}\n\n"
        
        # 先目录后文件
        dirs = sorted([f for f in files if f.is_dir()])
        files = sorted([f for f in files if f.is_file()])
        
        for d in dirs:
            result += f"📁 {d.name}/\n"
        for f in files:
            result += f"📄 {f.name}\n"
        
        return result
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def execute_command(command: str, timeout: int = 30, workdir: Optional[str] = None) -> str:
    """
    执行 Shell 命令
    
    Args:
        command: 要执行的命令
        timeout: 超时时间（秒，默认 30）
        workdir: 工作目录（默认当前目录）
        
    Returns:
        命令输出
    """
    # 安全检查
    dangerous = ['rm -rf', 'sudo', 'mkfs', 'dd', '> /dev/', 'curl | bash', 'wget | bash']
    if any(d in command for d in dangerous):
        return f"错误：禁止执行危险命令 - {command}"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir
        )
        
        output = ""
        if result.stdout:
            output += f"输出:\n{result.stdout}\n"
        if result.stderr:
            output += f"错误:\n{result.stderr}\n"
        
        return output or f"命令执行成功（无输出）\n返回码：{result.returncode}"
    
    except subprocess.TimeoutExpired:
        return f"错误：命令执行超时（>{timeout}秒）"
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def search_files(pattern: str, directory: str = ".") -> str:
    """
    搜索文件（支持 glob 模式）
    
    Args:
        pattern: 文件模式（如 "**/*.py"）
        directory: 搜索目录（默认当前目录）
        
    Returns:
        匹配的文件列表
    """
    path = Path(directory)
    
    if not path.exists():
        return f"错误：目录不存在 - {directory}"
    
    try:
        files = list(path.rglob(pattern))
        
        # 排除隐藏目录
        files = [f for f in files if '.git' not in str(f) and '__pycache__' not in str(f)]
        
        if not files:
            return f"未找到匹配的文件：{pattern}"
        
        result = f"找到 {len(files)} 个文件:\n\n"
        for f in files[:50]:  # 限制显示数量
            result += f"- {f.relative_to(path)}\n"
        
        if len(files) > 50:
            result += f"\n... 还有 {len(files) - 50} 个文件"
        
        return result
    except Exception as e:
        return f"错误：{str(e)}"


@tool
def search_content(pattern: str, directory: str = ".", file_pattern: str = "*") -> str:
    """
    搜索文件内容（grep）
    
    Args:
        pattern: 搜索模式（正则表达式）
        directory: 搜索目录
        file_pattern: 文件模式（如 "*.py"）
        
    Returns:
        匹配结果
    """
    path = Path(directory)
    
    if not path.exists():
        return f"错误：目录不存在 - {directory}"
    
    try:
        import re
        
        matches = []
        for file in path.rglob(file_pattern):
            if file.is_file() and '.git' not in str(file):
                try:
                    content = file.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            matches.append(f"{file.relative_to(path)}:{i}: {line.strip()}")
                except:
                    continue
        
        if not matches:
            return f"未找到匹配的内容：{pattern}"
        
        result = f"找到 {len(matches)} 处匹配:\n\n"
        for match in matches[:20]:  # 限制显示数量
            result += f"{match}\n"
        
        if len(matches) > 20:
            result += f"\n... 还有 {len(matches) - 20} 处匹配"
        
        return result
    except Exception as e:
        return f"错误：{str(e)}"


def get_all_tools() -> List:
    """获取所有工具"""
    return [
        read_file,
        write_file,
        edit_file,
        list_directory,
        execute_command,
        search_files,
        search_content,
    ]
