"""
DeepAgent 封装模块
基于 DeepAgents 框架构建的 AI Agent
提供流式对话、工具调用等核心功能
"""

import asyncio
import re
from pathlib import Path
from typing import AsyncIterator, Dict, Iterable, Optional, Tuple, Union, Any

from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

from core.config_manager import get_config_manager
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
    # 加载内置提示词
    prompts_content = _load_prompts_from_dir(BuiltinPaths.PROMPT_ROOT)

    if prompts_content:
        logger.info(f"已加载提示词文件从: {BuiltinPaths.PROMPT_ROOT}")
        return prompts_content

    # 如果没有提示词文件，使用默认提示词
    logger.warning("未找到提示词文件，使用默认提示词")
    return DEFAULT_SYSTEM_PROMPT


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
        # 使用 MemorySaver 作为 checkpointer，确保工具执行后状态正确保存
        self._checkpointer = MemorySaver()

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

            self.agent = create_deep_agent(
                model=self.llm,
                tools=ALL_TOOLS,
                system_prompt=system_prompt,
                checkpointer=self._checkpointer,
                debug=True,  # 启用调试模式
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

        # 构建当前用户消息
        if project_path:
            current_message = f"{user_input}\n\n[系统信息] 当前项目路径: {project_path}"
        else:
            current_message = user_input

        # 从 checkpointer 获取历史消息
        messages: list[Dict[str, str]] = []
        try:
            state = self._checkpointer.get(config)
            channel_values = state.get("channel_values") if state else None
            history: Iterable[Any] = (
                channel_values.get("messages", []) if channel_values else []
            )

            for msg in history:
                content = getattr(msg, "content", None)
                if not content:
                    continue

                msg_type = getattr(msg, "type", "")
                if msg_type == "human":
                    role = "user"
                elif msg_type == "ai":
                    role = "assistant"
                else:
                    # 默认按 user 处理，避免异常中断
                    role = "user"

                messages.append({"role": role, "content": content})

            if messages:
                logger.info(f"会话 {session_id[:8]}：加载历史 {len(messages)} 条")
        except Exception as e:  # pragma: no cover - 防御性分支
            logger.debug(f"获取历史失败: {e}")

        # 添加当前用户消息
        messages.append({"role": "user", "content": current_message})

        # 调试日志
        logger.info(
            f"会话 {session_id[:8]}：共 {len(messages)} 条消息，输入: {user_input[:50]}...")

        try:
            # 调试: 查看 agent 的工具信息
            if hasattr(self.agent, 'nodes'):
                for node_name, node in self.agent.nodes.items():
                    if hasattr(node, 'tools_by_name'):
                        logger.info(
                            f"Node {node_name} 工具: {list(node.tools_by_name.keys())}")

            async for chunk in self.agent.astream(
                {"messages": messages},
                config=config,
                stream_mode=["messages", "updates"],
            ):
                if self._stop_requested:
                    yield "\n\n[已中断]"
                    break

                chunk_type, data = self._parse_chunk(chunk)
                if not chunk_type:
                    continue

                if chunk_type == "messages":
                    async for text in self._iter_message_chunk(data):
                        yield text
                elif chunk_type == "updates":
                    async for text in self._iter_update_chunk(data):
                        yield text

        except asyncio.CancelledError:
            logger.info("流式响应被取消")
            yield "\n\n[已中断]"
        except Exception as e:
            logger.error(f"流式对话错误: {e}")
            yield f"\n\n❌ 发生错误: {str(e)}"

    @staticmethod
    def _parse_chunk(
        chunk: Union[Dict[str, Any], Tuple[Any, Any]]
    ) -> Tuple[Optional[str], Optional[Any]]:
        """
        将 deepagents 返回的 chunk 标准化为 (chunk_type, data)
        支持 dict 和 (mode, data) 两种格式。
        """
        if isinstance(chunk, dict):
            return chunk.get("type"), chunk.get("data")

        if isinstance(chunk, tuple) and len(chunk) >= 2:
            # (stream_mode, data) 格式
            return chunk[0], chunk[1]

        logger.debug(f"未知 chunk 格式: {chunk!r}")
        return None, None

    async def _iter_message_chunk(self, data: Any) -> AsyncIterator[str]:
        """
        解析 LLM 消息流 chunk，产出纯文本。
        """
        # 流式 LLM 输出: (token, metadata)
        token = data[0] if isinstance(data, tuple) and data else data
        content = getattr(token, "content", None)
        if not content:
            return

        if isinstance(content, str):
            yield content
            return

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        yield text

    async def _iter_update_chunk(self, data: Any) -> AsyncIterator[str]:
        """
        解析工具执行相关的 update chunk，生成用户可读的工具执行结果摘要。
        """
        if not isinstance(data, dict):
            return

        tools_update = data.get("tools")
        if not (isinstance(tools_update, dict) and "messages" in tools_update):
            return

        for msg in tools_update["messages"]:
            tool_name = getattr(msg, "name", None)
            if not tool_name:
                continue

            display_name = self._get_tool_display_name(tool_name)
            content = getattr(msg, "content", "")
            logger.info(f"工具完成: {tool_name}")

            if not content:
                continue

            display_output = str(content)[:500]
            yield (
                f"\n✅ {display_name} 完成\n```\n{display_output}\n```\n"
            )


def create_agent(temperature: float = 0.7) -> DeepAgentWrapper:
    """
    创建 DeepAgent 实例的便捷函数

    Args:
        temperature: LLM 温度参数

    Returns:
        DeepAgentWrapper 实例
    """
    return DeepAgentWrapper(temperature=temperature)
