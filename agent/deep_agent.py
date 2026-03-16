"""
DeepAgent 封装模块
基于 DeepAgents 框架构建的 AI Agent
提供流式对话、工具调用等核心功能
"""

import asyncio
import re
from pathlib import Path
from typing import AsyncIterator, Dict, Optional

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, CompositeBackend, StateBackend, StoreBackend

from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from core.config_manager import get_config_manager
from core.prompt_manager import get_prompt_manager

from llm_factory import get_llm
from utils.logger import get_logger
from constants.builtin_paths import BuiltinPaths

from .tools import ALL_TOOLS

logger = get_logger("agent.deep_agent")

# 获取全局配置管理器实例
_config = get_config_manager()


def _load_prompts_from_dir(prompts_dir: Path) -> str:
    """
    从目录加载所有提示词文件

    Args:
        prompts_dir: 提示词目录路径

    Returns:
        合并后的提示词内容
    """
    if not prompts_dir.exists():
        logger.debug(f"提示词目录不存在: {prompts_dir}")
        return ""

    prompts = []

    # 按文件名排序加载（如 01_role.md, 02_capabilities.md）
    for file_path in sorted(prompts_dir.glob("*.md")):
        try:
            content = file_path.read_text(encoding='utf-8')

            # 解析 frontmatter 检查 enabled 状态
            enabled = True
            frontmatter_match = re.match(
                r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)
                enabled_match = re.search(
                    r'^enabled:\s*(true|false)$', frontmatter, re.MULTILINE | re.IGNORECASE)
                if enabled_match:
                    enabled = enabled_match.group(1).lower() == 'true'

                # 移除 frontmatter
                content = content[frontmatter_match.end():]

            if enabled and content.strip():
                prompts.append(content.strip())
                logger.debug(f"加载提示词: {file_path.name}")

        except Exception as e:
            logger.error(f"加载提示词失败 {file_path}: {e}")

    return "\n\n".join(prompts)


def _build_system_prompt() -> str:
    """
    构建完整的系统提示词
    从 .agent/prompts 目录加载提示词文件
    """
    # # 加载内置提示词
    # prompts_content = _load_prompts_from_dir(BuiltinPaths.PROMPT_ROOT)

    # if prompts_content:
    #     logger.info(f"已加载提示词文件从: {BuiltinPaths.PROMPT_ROOT}")
    #     return prompts_content

    # # 如果没有提示词文件，使用默认提示词
    # logger.warning("未找到提示词文件，使用默认提示词")
    # return DEFAULT_SYSTEM_PROMPT

    manager = get_prompt_manager()
    return manager.build_system_prompt()


def make_prod_backend(rt):
    project_path = _config.get_current_project_path()
    return CompositeBackend(
        default=StateBackend(rt),                    # 临时笔记
        routes={
            "/memories/": StoreBackend(rt),          # 用户记忆
            "/workspace/": FilesystemBackend(project_path)  # 真实文件
        }
    )


# 默认系统提示词（备用）
DEFAULT_SYSTEM_PROMPT = """你是一个强大的 AI 助手，专门帮助用户完成各种编程和软件开发任务。

## 核心能力
1. **代码分析**: 语法检查、依赖分析、代码统计
2. **版本控制**: Git 操作（提交、推送、分支管理等）
3. **网络访问**: 网页获取、搜索引擎、API 请求
4. **文件管理**: 读写文件、目录操作
5. **任务规划**: 复杂任务分解、进度跟踪

请根据用户的需求，灵活运用你的能力来完成任务。"""


class DeepAgentWrapper:
    """
    DeepAgent 封装类
    提供与 Flet UI 兼容的流式对话接口
    """

    # 工具名中文映射（包含 deepagents 内置工具和自定义工具）
    TOOL_NAME_MAP = {
        # deepagents 内置工具
        "ls": "列出目录",
        "read_file": "读取文件",
        "write_file": "写入文件",
        "edit_file": "编辑文件",
        "glob": "文件搜索",
        "grep": "内容搜索",
        "execute": "执行命令",
        "write_todos": "管理任务",
        "task": "调用子代理",
        # 自定义工具（Git）
        "git_status": "Git 状态",
        "git_log": "Git 日志",
        "git_add": "Git 添加",
        "git_commit": "Git 提交",
        "git_push": "Git 推送",
        "git_pull": "Git 拉取",
        "git_branch": "Git 分支",
        "git_checkout": "Git 切换分支",
        "git_diff": "Git 差异",
        "git_clone": "Git 克隆",
        "git_init": "Git 初始化",
        # 自定义工具（代码分析）
        "check_syntax": "语法检查",
        "analyze_dependencies": "依赖分析",
        "code_statistics": "代码统计",
        # 自定义工具（网络）
        "fetch_webpage": "获取网页",
        "web_search": "网络搜索",
        "http_request": "HTTP 请求",
        "query_wikipedia": "查询维基",
        "fetch_rss": "获取RSS",
    }

    def __init__(self, temperature: float = 0.7):
        """
        初始化 DeepAgent

        Args:
            temperature: LLM 温度参数，控制生成随机性
        """
        self.temperature = temperature
        self.llm = None
        self.agent = None
        self._is_initialized = False
        self._stop_requested = False
        # 尝试初始化
        self._initialize()

    def _initialize(self):
        """初始化 Agent"""
        try:
            if not _config.is_llm_configured():
                logger.warning("LLM 未配置，Agent 初始化跳过")
                return

            # 获取 LLM 实例
            self.llm = get_llm(self.temperature)

            # 创建 DeepAgent
            # DeepAgents 内置了文件系统工具、任务规划工具等
            # 内置工具: ls, read_file, write_file, edit_file, glob, grep, execute, write_todos, task
            # 我们添加自定义的代码分析、Git、网络工具
            # 加载系统提示词
            system_prompt = _build_system_prompt()

            # 日志记录工具信息
            logger.info(f"自定义工具数量: {len(ALL_TOOLS)}")
            for tool in ALL_TOOLS:
                tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                logger.info(f"  - {tool_name}")

            else:
                logger.warning("未设置项目路径，deepagents 内置工具可能无法正常工作")

            self.agent = create_deep_agent(
                backend=make_prod_backend,
                model=self.llm,
                tools=ALL_TOOLS,
                system_prompt=system_prompt,
                debug=True,  # 启用调试模式
                store=InMemoryStore(),
            )

            self._is_initialized = True
            logger.info("DeepAgent 初始化成功")

        except Exception as e:
            logger.error(f"DeepAgent 初始化失败: {e}")
            self._is_initialized = False

    @property
    def is_ready(self) -> bool:
        """检查 Agent 是否就绪"""
        return self._is_initialized and self.agent is not None

    def reinitialize(self, temperature: Optional[float] = None):
        """
        重新初始化 Agent（例如配置更新后）

        Args:
            temperature: 新的温度参数（可选）
        """
        if temperature is not None:
            self.temperature = temperature
        self._initialize()

    def _get_tool_display_name(self, tool_name: str) -> str:
        """获取工具的中文显示名称"""
        return self.TOOL_NAME_MAP.get(tool_name, tool_name)

    async def stream_chat(
        self,
        user_input: str,
        project_path: str = "",
        session_id: str = "default",
    ) -> AsyncIterator[str]:
        """
        流式对话方法

        Args:
            user_input: 用户输入
            project_path: 当前项目路径
            session_id: 会话ID，用于区分不同对话的上下文

        Yields:
            流式响应内容（增量）
        """
        if not self.is_ready:
            yield "❌ Agent 未就绪，请先配置 LLM"
            return

        self._stop_requested = False
        config: Dict[str, Dict[str, str]] = {
            "configurable": {"thread_id": session_id}
        }

        messages = []
        # 构建当前用户消息
        if project_path:
            current_message = f"{user_input}\n\n[系统信息] 当前项目路径: {project_path}"
        else:
            current_message = user_input

        messages.append({"role": "user", "content": current_message})

        try:
            # 调试: 查看 agent 的工具信息
            if hasattr(self.agent, 'nodes'):
                for node_name, node in self.agent.nodes.items():
                    if hasattr(node, 'tools_by_name'):
                        logger.info(
                            f"Node {node_name} 工具: {list(node.tools_by_name.keys())}")

            async for event in self.agent.astream_events(
                {"messages": messages},
                config=config,
                version="v2",
            ):
                if self._stop_requested:
                    yield "\n\n[已中断]"
                    break

                # 1. 处理 LLM 生成的 token
                event_type = event.get("event")
                if not event_type:
                    continue

                if event_type == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and isinstance(chunk.content, str):
                        yield chunk.content

                # 2. 处理工具执行完成的事件
                elif event_type == "on_tool_end":
                    tool_name = event["name"]
                    yield f"\n\n✅ {self._get_tool_display_name(tool_name)} 已完成\n"

                # 3. 处理错误
                elif event_type == "on_chain_error":
                    yield f"\n\n❌ 发生错误: {event['data'].get('error')}"

        except asyncio.CancelledError:
            logger.info("流式响应被取消")
            yield "\n\n[已中断]"
        except Exception as e:
            logger.error(f"流式对话错误: {e}")
            yield f"\n\n❌ 发生错误: {str(e)}"


def create_agent(temperature: float = 0.7) -> DeepAgentWrapper:
    """
    创建 DeepAgent 实例的便捷函数

    Args:
        temperature: LLM 温度参数

    Returns:
        DeepAgentWrapper 实例
    """
    return DeepAgentWrapper(temperature=temperature)
