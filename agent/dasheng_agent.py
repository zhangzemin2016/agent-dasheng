"""
Dasheng Agent - 基于 LangChain + LangGraph 的自研 Agent
"""

import asyncio
from typing import TypedDict, Annotated, List, Optional, Dict, Any
from pathlib import Path
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
        
        # 调用 LLM
        response = self.llm.invoke(state["messages"])
        
        return {
            "messages": [response],
            "last_response": response.content if hasattr(response, 'content') else str(response)
        }
    
    def _tool_node(self, state: AgentState) -> Dict:
        """工具执行节点"""
        logger.debug("工具执行节点")
        
        # TODO: 实现工具执行逻辑
        # 目前先返回空消息，后续完善
        
        return {
            "messages": [AIMessage(content="工具执行中...")]
        }
    
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
        
        content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # 简单的路由逻辑（后续可以优化）
        # 检测是否需要调用工具
        if any(keyword in content.lower() for keyword in ['execute', 'run', 'file', 'git']):
            logger.debug("路由决策：使用工具")
            return "use_tools"
        
        # 检测是否需要调用技能
        if any(keyword in content.lower() for keyword in ['/skill', 'skill', '技能']):
            logger.debug("路由决策：使用技能")
            return "use_skills"
        
        # 检测是否需要继续对话
        if '?' in content or '？' in content:
            logger.debug("路由决策：继续对话")
            return "continue"
        
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
        logger.info(f"流式收到消息：{user_input[:50]}... (session={session_id})")
        
        # 获取历史消息
        from services.session_service import SessionService
        session_service = SessionService()
        session = session_service.get_current_session()
        history = session["messages"] if session else []
        
        # 调用 LLM 流式接口
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
        messages.append(HumanMessage(content=message))
        
        # 添加系统提示词
        system_prompt = self.prompt_manager.build_system_prompt()
        messages.insert(0, SystemMessage(content=system_prompt))
        
        # 流式调用 LLM
        try:
            async for chunk in self.llm.astream(messages):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                yield content
                await asyncio.sleep(0.01)  # 小延迟让 UI 更流畅
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
