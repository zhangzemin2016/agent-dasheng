"""Agent 工具模块"""
from .code_tools import check_syntax, analyze_dependencies, code_statistics
from .git_tools import (
    git_status, git_log, git_add, git_commit,
    git_push, git_pull, git_branch, git_checkout,
    git_diff, git_clone, git_init
)
from .network_tools import fetch_webpage, web_search, http_request, query_wikipedia, fetch_rss

# 所有工具列表
ALL_TOOLS = [
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

__all__ = [
    "ALL_TOOLS",
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
