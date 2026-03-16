"""
Dasheng Agent - 基于 LangChain + LangGraph 的自研 Agent
"""

import asyncio
from typing import TypedDict, Annotated, List, Optional, Dict
import operator

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool

from utils.logger import get_logger
from llm.langchain_factory import get_llm
from core.prompt_manager import get_prompt_manager
from core.skill_registry import get_skill_registry

logger = get_logger("agent.dasheng")


# ========== 状态定义 ==========

class AgentState(TypedDict):
    """Agent 状态"""
    messages: Annotated[List[BaseMessage], operator.add]  # 消息历史
    current_plan: Optional[Dict]  # 当前计划
    skills_context: str  # 技能上下文
    last_response: str  # 最后一条回复


# ========== Dasheng Agent 核心类 ==========

class DashengAgent:
    """
    大圣 Agent - 基于 LangChain + LangGraph

    架构：
    - LLM: LangChain (支持多提供商)
    - 流程控制：LangGraph 状态机
    - Prompt: 自研 DSL 系统
    - 技能：自研技能系统
    """

    def __init__(self, temperature: float = 0.7):
        self.temperature = temperature

        # 初始化组件
        logger.info("初始化 DashengAgent...")
        self.llm = get_llm(temperature=temperature)
        self.prompt_manager = get_prompt_manager()
        self.skill_registry = get_skill_registry()

        # 加载工具（按功能分类）
        from .tools import get_all_tools
        self.tools = get_all_tools()
        logger.info(f"DashengAgent 加载 {len(self.tools)} 个工具")

        # 绑定工具到 LLM（LangChain 工具绑定）
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # 构建 LangGraph 工作流
        self.graph = self._build_graph()

        self.is_ready = True
        logger.info("DashengAgent 初始化完成")

    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 工作流"""

        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("system_prompt", self._system_prompt_node)
        workflow.add_node("llm", self._llm_node)
        workflow.add_node("tools", self._tool_node)
        workflow.add_node("skills", self._skill_node)

        # 设置入口
        workflow.set_entry_point("system_prompt")

        # 添加边
        workflow.add_edge("system_prompt", "llm")
        workflow.add_conditional_edges(
            "llm",
            self._route_decision,
            {
                "use_tools": "tools",
                "use_skills": "skills",
                "end": END,
                "continue": "llm"
            }
        )
        workflow.add_edge("tools", "llm")
        workflow.add_edge("skills", "llm")

        # 编译
        return workflow.compile()

    def _system_prompt_node(self, state: AgentState) -> Dict:
        """系统提示词节点"""
        logger.debug("系统提示词节点")

        # 使用咱们的 Prompt DSL 构建系统提示词
        system_prompt = self.prompt_manager.build_system_prompt()

        # 添加技能上下文
        skills_context = self.skill_registry.get_all_skills_context()

        return {
            "skills_context": skills_context,
            "messages": [SystemMessage(content=system_prompt)]
        }

    def _llm_node(self, state: AgentState) -> Dict:
        """LLM 调用节点"""
        logger.debug(f"LLM 节点，消息数：{len(state['messages'])}")

        # 调用带工具的 LLM
        response = self.llm_with_tools.invoke(state["messages"])

        # 检查是否有工具调用
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.debug(f"LLM 返回工具调用：{len(response.tool_calls)} 个")

        return {
            "messages": [response],
            "last_response": response.content if hasattr(response, 'content') else str(response)
        }

    def _tool_node(self, state: AgentState) -> Dict:
        """工具执行节点"""
        logger.debug("工具执行节点")

        # 获取最后一条 AI 消息，检查工具调用
        last_message = state["messages"][-1] if state["messages"] else None
        if not last_message:
            return {"messages": [AIMessage(content="没有需要执行的操作")]}

        # 检查是否有工具调用
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            results = []
            for tool_call in last_message.tool_calls:
                result = self._execute_tool_call(tool_call)
                results.append(result)

            return {
                "messages": [AIMessage(content="\n\n".join(results))]
            }

        # 如果没有工具调用，返回提示
        return {
            "messages": [AIMessage(content="未检测到工具调用")]
        }

    def _execute_tool_call(self, tool_call, workdir: str = "") -> str:
        """
        执行工具调用

        Args:
            tool_call: LangChain 工具调用对象
            workdir: 工作目录（项目路径）

        Returns:
            执行结果
        """
        from .tools import get_all_tools

        tool_name = tool_call.get('name', '') if isinstance(
            tool_call, dict) else getattr(tool_call, 'name', '')
        tool_args = tool_call.get('args', {}) if isinstance(
            tool_call, dict) else getattr(tool_call, 'args', {})

        # 如果是命令执行工具，注入工作目录
        if tool_name == 'execute_command' and workdir:
            tool_args['workdir'] = workdir
            logger.info(f"🔧 执行工具：{tool_name} (workdir={workdir})")
        else:
            logger.info(f"🔧 执行工具：{tool_name}")

        # 查找工具
        tools = {tool.name: tool for tool in get_all_tools()}

        if tool_name not in tools:
            return f"❌ 错误：未找到工具 - {tool_name}"

        try:
            # 执行工具
            result = tools[tool_name].invoke(tool_args)
            return f"✅ {tool_name}:\n{result}"
        except Exception as e:
            return f"❌ {tool_name} 失败：{str(e)}"

    def _skill_node(self, state: AgentState) -> Dict:
        """技能执行节点"""
        logger.debug("技能执行节点")

        # TODO: 实现技能执行逻辑
        # 目前先返回空消息，后续完善

        return {
            "messages": [AIMessage(content="技能执行中...")]
        }

    def _route_decision(self, state: AgentState) -> str:
        """路由决策：判断下一步该做什么"""
        last_message = state["messages"][-1] if state["messages"] else None

        if not last_message:
            return "end"

        # 检查是否有工具调用（优先）
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            logger.debug(f"路由决策：使用工具 ({len(last_message.tool_calls)} 个)")
            return "use_tools"

        # 检查是否需要调用技能
        content = last_message.content if hasattr(
            last_message, 'content') else str(last_message)
        if any(keyword in content.lower() for keyword in ['/skill', 'skill', '技能']):
            logger.debug("路由决策：使用技能")
            return "use_skills"

        # 默认结束
        logger.debug("路由决策：结束")
        return "end"

    async def chat(self, message: str, history: List[Dict] = None) -> str:
        """
        处理用户消息

        Args:
            message: 用户消息
            history: 历史消息列表 [{"role": "user|assistant", "content": "..."}]

        Returns:
            AI 回复内容
        """
        logger.info(f"收到消息：{message[:50]}...")

        # 转换历史消息为 LangChain 格式
        messages = []
        if history:
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))

        # 添加当前消息
        messages.append(HumanMessage(content=message))

        # 初始化状态
        state = AgentState(
            messages=messages,
            current_plan=None,
            skills_context="",
            last_response=""
        )

        # 运行工作流
        result = await self.graph.ainvoke(state)

        # 获取最后一条回复
        response = result.get("last_response", "")

        logger.info(f"AI 回复：{response[:50]}...")
        return response

    async def stream_chat(
        self,
        user_input: str,
        project_path: str = "",
        session_id: str = "default"
    ):
        """
        流式处理用户消息（保持 UI 兼容性）

        Args:
            user_input: 用户消息
            project_path: 项目路径（用于上下文）
            session_id: 会话 ID

        Yields:
            文本块
        """
        logger.info(f"流式收到消息：{user_input[:50]}... (session={session_id}, project={project_path or 'default'})")

        # 获取当前项目路径（如果未传入）
        if not project_path:
            from services.project_service import ProjectService
            project_service = ProjectService()
            project_path = project_service.get_current_project() or ""
        
        logger.debug(f"使用项目路径：{project_path}")

        # 获取历史消息
        from services.session_service import SessionService
        session_service = SessionService()
        session = session_service.get_current_session()
        history = session["messages"] if session else []

        # 转换历史消息为 LangChain 格式
        messages = []
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        # 添加当前消息
        messages.append(HumanMessage(content=user_input))

        # 添加系统提示词
        system_prompt = self.prompt_manager.build_system_prompt()
        messages.insert(0, SystemMessage(content=system_prompt))

        # 先调用 LLM（带工具绑定）判断是否需要执行工具
        try:
            # 使用带工具的 LLM 调用
            response = await self.llm_with_tools.ainvoke(messages)

            # 检查是否有工具调用
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info(f"检测到 {len(response.tool_calls)} 个工具调用")

                # 执行工具（传入项目路径作为工作目录）
                for tool_call in response.tool_calls:
                    result = self._execute_tool_call(tool_call, workdir=project_path)
                    yield f"{result}\n"

                return

            # 没有工具调用，流式输出内容
            if hasattr(response, 'content') and response.content:
                content = response.content
                # 模拟流式输出
                for i in range(0, len(content), 10):
                    chunk = content[i:i+10]
                    yield chunk
                    await asyncio.sleep(0.01)
            else:
                yield "无响应内容"

        except Exception as e:
            logger.error(f"流式调用失败：{e}")
            yield f"[错误：{str(e)}]"

    def chat_sync(self, message: str, history: List[Dict] = None) -> str:
        """同步版本的 chat 方法"""
        return asyncio.run(self.chat(message, history))


# ========== 工厂函数 ==========

def create_agent(temperature: float = 0.7) -> DashengAgent:
    """
    创建 DashengAgent 实例

    Args:
        temperature: 温度参数 (0-1)

    Returns:
        DashengAgent 实例
    """
    return DashengAgent(temperature=temperature)
