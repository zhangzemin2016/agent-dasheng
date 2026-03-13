"""Agent 工具聚合模块。

这里集中导出所有提供给 deepagents 使用的 LangChain 工具。
"""

from typing import Sequence

from .code_tools import analyze_dependencies, check_syntax, code_statistics
from .git_tools import (
    git_add,
    git_branch,
    git_checkout,
    git_clone,
    git_commit,
    git_diff,
    git_init,
    git_log,
    git_pull,
    git_push,
    git_status,
)
from .network_tools import (
    fetch_rss,
    fetch_webpage,
    http_request,
    query_wikipedia,
    web_search,
)


def _build_all_tools() -> list:
    """构建当前可用的工具列表。

    单独封装一层，方便未来按配置开关或动态增减工具。
    """
    tools: list = [
        # 代码分析工具
        check_syntax,
        analyze_dependencies,
        code_statistics,
        # Git 工具
        git_status,
        git_log,
        git_add,
        git_commit,
        git_push,
        git_pull,
        git_branch,
        git_checkout,
        git_diff,
        git_clone,
        git_init,
        # 网络工具
        fetch_webpage,
        web_search,
        http_request,
        query_wikipedia,
        fetch_rss,
    ]
    return tools


# 供 deep_agent 使用的统一工具列表
ALL_TOOLS: Sequence = tuple(_build_all_tools())

__all__ = (
    [
        "ALL_TOOLS",
        "_build_all_tools",
        "check_syntax",
        "analyze_dependencies",
        "code_statistics",
        "git_status",
        "git_log",
        "git_add",
        "git_commit",
        "git_push",
        "git_pull",
        "git_branch",
        "git_checkout",
        "git_diff",
        "git_clone",
        "git_init",
        "fetch_webpage",
        "web_search",
        "http_request",
        "query_wikipedia",
        "fetch_rss",
    ]
)
