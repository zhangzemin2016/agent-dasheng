"""
Git 操作工具
提供版本控制相关功能
"""

import os
import subprocess
from typing import Optional
from langchain_core.tools import tool


def _get_project_path() -> Optional[str]:
    """获取当前项目路径"""
    try:
        from core.config_manager import get_config_manager
        return get_config_manager().get_current_project_path()
    except:
        return None


def _run_git_command(args: list, cwd: str = None, workdir: Optional[str] = None) -> tuple:
    """运行 git 命令并返回结果"""
    try:
        project_path = _get_project_path()

        # 优先使用传入的 workdir，其次使用 cwd，最后使用项目路径
        if workdir:
            cwd = workdir
        elif cwd is None:
            cwd = project_path or os.getcwd()

        # 安全检查：确保工作目录在项目路径下
        if project_path:
            cwd_normalized = os.path.normpath(os.path.abspath(cwd))
            project_path_normalized = os.path.normpath(
                os.path.abspath(project_path))
            if not cwd_normalized.startswith(project_path_normalized):
                return -1, "", f"安全限制：只能操作项目路径 '{project_path}' 下的 Git 仓库"

        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"
    except FileNotFoundError:
        return -1, "", "未找到 git 命令，请安装 Git"
    except Exception as e:
        return -1, "", str(e)


@tool
def git_status(path: str = ".", workdir: Optional[str] = None) -> str:
    """
    查看 Git 仓库状态

    Args:
        repo_path: 仓库路径，默认为当前目录
        workdir: 工作目录/项目路径

    Returns:
        Git 状态信息
    """
    try:
        returncode, stdout, stderr = _run_git_command(
            ['status'], path, workdir=workdir)

        if returncode == 0:
            return f"📋 Git 状态:\n\n{stdout}"
        else:
            return f"❌ 错误：{stderr}"
    except Exception as e:
        return f"❌ 执行出错：{str(e)}"


@tool
def git_log(path: str = ".", max_count: int = 10, workdir: Optional[str] = None) -> str:
    """
    查看 Git 提交历史

    Args:
        repo_path: 仓库路径
        max_count: 最大显示条数
        workdir: 工作目录/项目路径

    Returns:
        提交历史
    """
    try:
        returncode, stdout, stderr = _run_git_command(
            ['log', f'-{max_count}', '--oneline'], path, workdir=workdir)

        if returncode == 0:
            return f"📜 Git 提交历史:\n\n{stdout}"
        else:
            return f"❌ 错误：{stderr}"
    except Exception as e:
        return f"❌ 执行出错：{str(e)}"


@tool
def git_add(path: str = ".", files: str = ".", workdir: Optional[str] = None) -> str:
    """
    添加文件到 Git 暂存区

    Args:
        repo_path: 仓库路径
        files: 要添加的文件（支持通配符）
        workdir: 工作目录/项目路径

    Returns:
        操作结果
    """
    try:
        returncode, stdout, stderr = _run_git_command(
            ['add', files], path, workdir=workdir)

        if returncode == 0:
            return f"✅ 已添加到暂存区：{files}"
        else:
            return f"❌ 错误：{stderr}"
    except Exception as e:
        return f"❌ 执行出错：{str(e)}"


@tool
def git_commit(path: str = ".", message: str = "", allow_empty: bool = False, workdir: Optional[str] = None) -> str:
    """
    提交 Git 变更

    Args:
        repo_path: 仓库路径
        message: 提交信息
        allow_empty: 是否允许空提交
        workdir: 工作目录/项目路径

    Returns:
        提交结果
    """
    try:
        if not message:
            return "❌ 错误：提交信息不能为空"

        args = ['commit', '-m', message]
        if allow_empty:
            args.append('--allow-empty')

        returncode, stdout, stderr = _run_git_command(
            args, path, workdir=workdir)

        if returncode == 0:
            return f"✅ Git 提交成功:\n{stdout}"
        else:
            return f"❌ 错误：{stderr}"
    except Exception as e:
        return f"❌ 执行出错：{str(e)}"


@tool
def git_push(path: str = ".", remote: str = "origin", branch: str = None, workdir: Optional[str] = None) -> str:
    """
    推送 Git 提交到远程仓库

    Args:
        repo_path: 仓库路径
        remote: 远程仓库名
        branch: 分支名（可选）
        workdir: 工作目录/项目路径

    Returns:
        推送结果
    """
    try:
        args = ['push', remote]
        if branch:
            args.append(branch)

        returncode, stdout, stderr = _run_git_command(
            args, path, workdir=workdir)

        if returncode == 0:
            return f"✅ Git 推送成功:\n{stdout}"
        else:
            return f"❌ 错误：{stderr}"
    except Exception as e:
        return f"❌ 执行出错：{str(e)}"


@tool
def git_pull(path: str = ".", remote: str = "origin", branch: str = None, workdir: Optional[str] = None) -> str:
    """
    从远程仓库拉取更新

    Args:
        repo_path: 仓库路径
        remote: 远程仓库名
        branch: 分支名（可选）
        workdir: 工作目录/项目路径

    Returns:
        拉取结果
    """
    try:
        args = ['pull', remote]
        if branch:
            args.append(branch)

        returncode, stdout, stderr = _run_git_command(
            args, path, workdir=workdir)

        if returncode == 0:
            return f"✅ Git 拉取成功:\n{stdout}"
        else:
            return f"❌ 错误：{stderr}"
    except Exception as e:
        return f"❌ 执行出错：{str(e)}"


@tool
def git_branch_list(path: str = ".", workdir: Optional[str] = None) -> str:
    """
    查看 Git 分支列表

    Args:
        repo_path: 仓库路径
        workdir: 工作目录/项目路径

    Returns:
        分支列表
    """
    try:
        returncode, stdout, stderr = _run_git_command(
            ['branch', '-a'], path, workdir=workdir)

        if returncode == 0:
            return f"🌿 Git 分支:\n\n{stdout}"
        else:
            return f"❌ 错误：{stderr}"
    except Exception as e:
        return f"❌ 执行出错：{str(e)}"


@tool
def git_checkout_branch(path: str = ".", branch: str = "", workdir: Optional[str] = None) -> str:
    """
    切换到指定分支

    Args:
        repo_path: 仓库路径
        branch: 分支名
        workdir: 工作目录/项目路径

    Returns:
        切换结果
    """
    try:
        if not branch:
            return "❌ 错误：分支名不能为空"

        returncode, stdout, stderr = _run_git_command(
            ['checkout', branch], path, workdir=workdir)

        if returncode == 0:
            return f"✅ 已切换到分支：{branch}"
        else:
            return f"❌ 错误：{stderr}"
    except Exception as e:
        return f"❌ 执行出错：{str(e)}"


@tool
def git_diff(path: str = ".", staged: bool = False, workdir: Optional[str] = None) -> str:
    """
    查看 Git 差异

    Args:
        repo_path: 仓库路径
        staged: 是否查看暂存区差异
        workdir: 工作目录/项目路径

    Returns:
        差异内容
    """
    try:
        args = ['diff']
        if staged:
            args.append('--cached')

        returncode, stdout, stderr = _run_git_command(
            args, path, workdir=workdir)

        if returncode == 0:
            if stdout:
                return f"📝 Git 差异:\n\n{stdout}"
            else:
                return "✅ 没有差异"
        else:
            return f"❌ 错误：{stderr}"
    except Exception as e:
        return f"❌ 执行出错：{str(e)}"


@tool
def git_init(path: str = ".", workdir: Optional[str] = None) -> str:
    """
    初始化 Git 仓库

    Args:
        repo_path: 仓库路径
        workdir: 工作目录/项目路径

    Returns:
        初始化结果
    """
    try:
        returncode, stdout, stderr = _run_git_command(
            ['init'], path, workdir=workdir)

        if returncode == 0:
            return f"✅ Git 仓库初始化成功:\n{stdout}"
        else:
            return f"❌ 错误：{stderr}"
    except Exception as e:
        return f"❌ 执行出错：{str(e)}"


@tool
def git_clone(url: str, destination: str = None, workdir: Optional[str] = None) -> str:
    """
    克隆 Git 仓库

    Args:
        url: 仓库 URL
        destination: 目标目录（可选）
        workdir: 工作目录/项目路径

    Returns:
        克隆结果
    """
    try:
        args = ['clone', url]
        if destination:
            args.append(destination)

        returncode, stdout, stderr = _run_git_command(args, workdir=workdir)

        if returncode == 0:
            return f"✅ Git 克隆成功:\n{stdout}"
        else:
            return f"❌ 错误：{stderr}"
    except Exception as e:
        return f"❌ 执行出错：{str(e)}"


def get_git_tools():
    """获取所有 Git 工具"""
    return [
        git_status,
        git_log,
        git_add,
        git_commit,
        git_push,
        git_pull,
        git_branch_list,
        git_checkout_branch,
        git_diff,
        git_init,
        git_clone,
    ]


# 工具名称映射（用于显示中文名称）
TOOL_DISPLAY_NAMES = {
    "git_status": "Git 状态",
    "git_log": "Git 提交历史",
    "git_add": "Git 添加文件",
    "git_commit": "Git 提交",
    "git_push": "Git 推送",
    "git_pull": "Git 拉取",
    "git_branch_list": "Git 分支列表",
    "git_checkout_branch": "Git 切换分支",
    "git_diff": "Git 查看差异",
    "git_init": "Git 初始化",
    "git_clone": "Git 克隆",
}
