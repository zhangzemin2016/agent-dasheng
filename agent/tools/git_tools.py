"""
Git 操作工具
提供版本控制相关功能
适配 DeepAgents 框架
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


def _run_git_command(args: list, cwd: str = None) -> tuple:
    """运行 git 命令并返回结果"""
    try:
        project_path = _get_project_path()

        # 如果没有指定 cwd，使用项目路径
        if cwd is None:
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


@tool("Git状态")
def git_status(repo_path: str = ".") -> str:
    """
    查看 Git 仓库状态

    Args:
        repo_path: 仓库路径，默认为当前目录

    Returns:
        Git 状态信息
    """
    try:
        returncode, stdout, stderr = _run_git_command(['status'], repo_path)

        if returncode == 0:
            return f"📋 Git 状态:\n\n{stdout}"
        else:
            return f"❌ 错误: {stderr}"
    except Exception as e:
        return f"❌ 执行出错: {str(e)}"


@tool("Git提交历史")
def git_log(repo_path: str = ".", max_count: int = 10) -> str:
    """
    查看 Git 提交历史

    Args:
        repo_path: 仓库路径，默认为当前目录
        max_count: 显示的最大提交数，默认为 10

    Returns:
        提交历史
    """
    try:
        returncode, stdout, stderr = _run_git_command(
            ['log', f'--max-count={max_count}',
                '--oneline', '--graph', '--decorate'],
            repo_path
        )

        if returncode == 0:
            return f"📜 最近 {max_count} 条提交:\n\n{stdout}"
        else:
            return f"❌ 错误: {stderr}"
    except Exception as e:
        return f"❌ 执行出错: {str(e)}"


@tool("Git添加文件")
def git_add(repo_path: str = ".", files: str = ".") -> str:
    """
    将文件添加到暂存区

    Args:
        repo_path: 仓库路径，默认为当前目录
        files: 要添加的文件路径（支持通配符），默认为所有更改

    Returns:
        操作结果
    """
    try:
        returncode, stdout, stderr = _run_git_command(
            ['add', files], repo_path)

        if returncode == 0:
            return f"✅ 已添加文件到暂存区: {files}"
        else:
            return f"❌ 错误: {stderr}"
    except Exception as e:
        return f"❌ 执行出错: {str(e)}"


@tool("Git提交")
def git_commit(repo_path: str = ".", message: str = "", allow_empty: bool = False) -> str:
    """
    提交暂存区的更改

    Args:
        repo_path: 仓库路径，默认为当前目录
        message: 提交信息
        allow_empty: 是否允许空提交，默认为 False

    Returns:
        操作结果
    """
    try:
        if not message:
            return "❌ 错误: 提交信息不能为空"

        args = ['commit', '-m', message]
        if allow_empty:
            args.append('--allow-empty')

        returncode, stdout, stderr = _run_git_command(args, repo_path)

        if returncode == 0:
            return f"✅ 提交成功:\n\n{stdout}"
        else:
            return f"❌ 错误: {stderr}"
    except Exception as e:
        return f"❌ 执行出错: {str(e)}"


@tool("Git推送")
def git_push(repo_path: str = ".", remote: str = "origin", branch: Optional[str] = None) -> str:
    """
    推送提交到远程仓库

    Args:
        repo_path: 仓库路径，默认为当前目录
        remote: 远程仓库名称，默认为 origin
        branch: 分支名称（可选，默认为当前分支）

    Returns:
        操作结果
    """
    try:
        args = ['push', remote]
        if branch:
            args.append(branch)

        returncode, stdout, stderr = _run_git_command(args, repo_path)

        if returncode == 0:
            return f"✅ 推送成功:\n\n{stdout}"
        else:
            return f"❌ 错误: {stderr}"
    except Exception as e:
        return f"❌ 执行出错: {str(e)}"


@tool("Git拉取")
def git_pull(repo_path: str = ".", remote: str = "origin", branch: Optional[str] = None) -> str:
    """
    从远程仓库拉取更新

    Args:
        repo_path: 仓库路径，默认为当前目录
        remote: 远程仓库名称，默认为 origin
        branch: 分支名称（可选）

    Returns:
        操作结果
    """
    try:
        args = ['pull', remote]
        if branch:
            args.append(branch)

        returncode, stdout, stderr = _run_git_command(args, repo_path)

        if returncode == 0:
            return f"✅ 拉取成功:\n\n{stdout}"
        else:
            return f"❌ 错误: {stderr}"
    except Exception as e:
        return f"❌ 执行出错: {str(e)}"


@tool("Git分支列表")
def git_branch(repo_path: str = ".") -> str:
    """
    查看分支列表

    Args:
        repo_path: 仓库路径，默认为当前目录

    Returns:
        分支列表
    """
    try:
        returncode, stdout, stderr = _run_git_command(
            ['branch', '-a'], repo_path)

        if returncode == 0:
            return f"🌿 分支列表:\n\n{stdout}"
        else:
            return f"❌ 错误: {stderr}"
    except Exception as e:
        return f"❌ 执行出错: {str(e)}"


@tool("Git切换分支")
def git_checkout(repo_path: str = ".", branch: Optional[str] = None, create: bool = False) -> str:
    """
    切换或创建分支

    Args:
        repo_path: 仓库路径，默认为当前目录
        branch: 分支名称
        create: 是否创建新分支，默认为 False

    Returns:
        操作结果
    """
    try:
        if not branch:
            return "❌ 错误: 分支名称不能为空"

        args = ['checkout']
        if create:
            args.append('-b')
        args.append(branch)

        returncode, stdout, stderr = _run_git_command(args, repo_path)

        if returncode == 0:
            action = "创建并切换到" if create else "切换到"
            return f"✅ {action}分支: {branch}\n\n{stdout}"
        else:
            return f"❌ 错误: {stderr}"
    except Exception as e:
        return f"❌ 执行出错: {str(e)}"


@tool("Git查看差异")
def git_diff(repo_path: str = ".", staged: bool = False, file: Optional[str] = None) -> str:
    """
    查看文件差异

    Args:
        repo_path: 仓库路径，默认为当前目录
        staged: 是否查看暂存区的差异，默认为 False
        file: 指定文件路径（可选）

    Returns:
        差异内容
    """
    try:
        args = ['diff']
        if staged:
            args.append('--staged')
        if file:
            args.append(file)

        returncode, stdout, stderr = _run_git_command(args, repo_path)

        if returncode == 0:
            if stdout:
                return f"📊 差异内容:\n\n{stdout[:2000]}" + ("\n... (内容已截断)" if len(stdout) > 2000 else "")
            else:
                return "✅ 没有差异"
        else:
            return f"❌ 错误: {stderr}"
    except Exception as e:
        return f"❌ 执行出错: {str(e)}"


@tool("Git初始化")
def git_init(repo_path: str = ".") -> str:
    """
    初始化 Git 仓库

    Args:
        repo_path: 仓库路径，默认为当前目录

    Returns:
        操作结果
    """
    try:
        returncode, stdout, stderr = _run_git_command(['init'], repo_path)

        if returncode == 0:
            return f"✅ Git 仓库初始化成功: {repo_path}\n\n{stdout}"
        else:
            return f"❌ 错误: {stderr}"
    except Exception as e:
        return f"❌ 执行出错: {str(e)}"


@tool("Git克隆")
def git_clone(repo_url: str, local_path: Optional[str] = None) -> str:
    """
    克隆远程仓库

    Args:
        repo_url: 远程仓库 URL
        local_path: 本地保存路径（可选，默认为仓库名）

    Returns:
        操作结果
    """
    try:
        if not repo_url:
            return "❌ 错误: 仓库 URL 不能为空"

        args = ['clone', repo_url]
        if local_path:
            args.append(local_path)

        returncode, stdout, stderr = _run_git_command(args)

        if returncode == 0:
            return f"✅ 克隆成功:\n\n{stdout}"
        else:
            return f"❌ 错误: {stderr}"
    except Exception as e:
        return f"❌ 执行出错: {str(e)}"
