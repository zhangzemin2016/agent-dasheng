"""
Agent 工具集

按功能分类：
- file_tools: 文件操作（读、写、编辑、删除、复制）
- directory_tools: 目录操作（列出、创建、删除、移动）
- command_tools: 命令执行（Shell、Python、脚本）
- search_tools: 搜索（文件、内容）
"""

from .file_tools import get_file_tools
from .directory_tools import get_directory_tools
from .command_tools import get_command_tools
from .search_tools import get_search_tools

from utils.logger import get_logger

logger = get_logger("agent.tools")


def get_all_tools():
    """获取所有工具"""
    tools = []
    
    # 文件操作工具
    tools.extend(get_file_tools())
    logger.debug(f"加载文件工具：{len(get_file_tools())} 个")
    
    # 目录操作工具
    tools.extend(get_directory_tools())
    logger.debug(f"加载目录工具：{len(get_directory_tools())} 个")
    
    # 命令行工具
    tools.extend(get_command_tools())
    logger.debug(f"加载命令工具：{len(get_command_tools())} 个")
    
    # 搜索工具
    tools.extend(get_search_tools())
    logger.debug(f"加载搜索工具：{len(get_search_tools())} 个")
    
    logger.info(f"总共加载 {len(tools)} 个工具")
    return tools


__all__ = [
    "get_all_tools",
    "get_file_tools",
    "get_directory_tools",
    "get_command_tools",
    "get_search_tools",
]
