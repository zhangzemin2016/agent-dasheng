"""
命令行执行工具集
"""

import subprocess
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from utils.logger import get_logger

logger = get_logger("agent.tools.command")

# 危险命令黑名单
DANGEROUS_COMMANDS = [
    'rm -rf',
    'sudo',
    'mkfs',
    'dd',
    '> /dev/',
    'curl | bash',
    'wget | bash',
    'curl | sh',
    'wget | sh',
    ':(){ :|:& };:',  # fork bomb
    'chmod -R 777',
    'chown -R',
]


@tool("执行 Shell 命令")
def execute_command(command: str, timeout: int = 30, workdir: Optional[str] = None, shell: bool = True) -> str:
    """
    执行 Shell 命令

    Args:
        command: 要执行的命令
        timeout: 超时时间（秒，默认 30）
        workdir: 工作目录（默认当前目录）
        shell: 是否使用 shell 执行

    Returns:
        命令输出
    """
    # 安全检查
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous in command:
            return f"🚫 禁止执行危险命令：{command}"

    logger.info(f"执行命令：{command} (timeout={timeout}s)")

    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir
        )

        output = ""

        if result.stdout:
            output += f"📤 输出:\n{result.stdout}\n"

        if result.stderr:
            output += f"⚠️ 错误:\n{result.stderr}\n"

        if not output:
            output = f"✅ 命令执行成功（无输出）\n返回码：{result.returncode}"
        else:
            output += f"\n返回码：{result.returncode}"

        return output

    except subprocess.TimeoutExpired:
        return f"⏱️ 错误：命令执行超时（>{timeout}秒）"
    except FileNotFoundError:
        return f"❌ 错误：命令不存在 - {command.split()[0] if command.split() else command}"
    except Exception as e:
        return f"❌ 错误：{str(e)}"


@tool("运行 Python 代码")
def run_python(code: str, timeout: int = 10) -> str:
    """
    运行 Python 代码片段

    Args:
        code: Python 代码
        timeout: 超时时间（秒）

    Returns:
        执行结果
    """
    # 安全检查
    dangerous = ['import os', 'import sys',
                 'subprocess', '__import__', 'eval(', 'exec(']
    for d in dangerous:
        if d in code:
            return f"🚫 禁止执行危险代码：包含 {d}"

    try:
        result = subprocess.run(
            ['python3', '-c', code],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        output = ""
        if result.stdout:
            output += f"输出:\n{result.stdout}\n"
        if result.stderr:
            output += f"错误:\n{result.stderr}\n"

        return output or "执行成功（无输出）"

    except subprocess.TimeoutExpired:
        return f"错误：执行超时（>{timeout}秒）"
    except Exception as e:
        return f"错误：{str(e)}"


@tool("运行脚本文件")
def run_script(script_path: str, args: str = "", timeout: int = 60) -> str:
    """
    运行脚本文件

    Args:
        script_path: 脚本路径
        args: 命令行参数
        timeout: 超时时间（秒）

    Returns:
        执行结果
    """
    path = Path(script_path)

    if not path.exists():
        return f"错误：脚本不存在 - {script_path}"

    if not path.is_file():
        return f"错误：不是文件 - {script_path}"

    command = f"{script_path} {args}".strip()

    return execute_command.invoke({
        "command": command,
        "timeout": timeout
    })


def get_command_tools():
    """获取所有命令行工具"""
    return [
        execute_command,
        run_python,
        run_script,
    ]
