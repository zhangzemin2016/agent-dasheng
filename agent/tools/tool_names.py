"""
工具名称映射
用于将工具函数名映射到中文显示名称
"""

# 所有工具的中文名称映射
TOOL_DISPLAY_NAMES = {
    # 文件操作工具
    "read_file": "读取文件",
    "write_file": "写入文件",
    "edit_file": "编辑文件",
    "delete_file": "删除文件",
    "copy_file": "复制文件",
    
    # 目录操作工具
    "list_directory": "列出目录内容",
    "create_directory": "创建目录",
    "delete_directory": "删除目录",
    "move_path": "移动文件或目录",
    
    # 搜索工具
    "search_files": "搜索文件",
    "search_content": "搜索内容",
    "find_in_files": "在文件中搜索",
    
    # 命令行工具
    "execute_command": "执行 Shell 命令",
    "run_python": "运行 Python 代码",
    "run_script": "运行脚本文件",
    
    # 代码分析工具
    "check_syntax": "语法检查",
    "analyze_dependencies": "依赖分析",
    "code_statistics": "代码统计",
    
    # Git 工具
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
    
    # 网络工具
    "fetch_webpage": "获取网页内容",
    "web_search": "网络搜索",
    "http_request": "HTTP 请求",
    "query_wikipedia": "查询维基百科",
    "fetch_rss": "获取 RSS 订阅",
}


def get_tool_display_name(tool_name: str) -> str:
    """
    获取工具的中文显示名称
    
    Args:
        tool_name: 工具函数名
    
    Returns:
        中文显示名称，如果没有映射则返回原名称
    """
    return TOOL_DISPLAY_NAMES.get(tool_name, tool_name)


def get_all_tool_names() -> dict:
    """
    获取所有工具名称映射
    
    Returns:
        工具名称映射字典
    """
    return TOOL_DISPLAY_NAMES.copy()
