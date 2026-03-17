"""
会话管理服务（增强版）
基于 LangChain 消息格式的会话管理

功能：
- 支持 LangChain 消息格式（HumanMessage, AIMessage, ToolMessage）
- 自动持久化到存储
- 上下文窗口管理
- 异步保存
"""

import time
import uuid
import asyncio
import copy
from typing import Dict, List, Optional, Any
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage

from utils.logger import get_logger
from storage.session_storage import get_session_storage

logger = get_logger("services.session")


class SessionService:
    """会话管理服务（增强版）"""

    def __init__(self):
        self.sessions: Dict[str, Dict] = {}  # 改为字典索引，提高查找效率
        self.current_session_id: Optional[str] = None
        self.storage = get_session_storage()

        # 上下文窗口配置
        self.max_context_messages = 50  # 最大保留消息数

        # 加载已有会话
        self._load_all_sessions()

    def _load_all_sessions(self):
        """从存储加载所有会话"""
        try:
            stored_sessions = self.storage.load_all_sessions()
            for session in stored_sessions:
                # 转换消息为 LangChain 格式
                session["messages"] = self._deserialize_messages(
                    session.get("messages", []))
                self.sessions[session["id"]] = session

            # 设置最后一个活动的会话为当前会话
            if self.sessions:
                # 按 updated_at 排序，最新的在前
                sorted_sessions = sorted(
                    self.sessions.values(),
                    key=lambda s: s.get("updated_at", 0),
                    reverse=True
                )
                self.current_session_id = sorted_sessions[0]["id"]
                logger.info(
                    f"加载了 {len(stored_sessions)} 个会话，当前会话：{self.current_session_id[:8]}")
        except Exception as e:
            logger.error(f"加载会话失败：{e}")
            # 如果加载失败，创建一个新会话
            self.create_session()

    # ========== 会话基础操作 ==========

    def create_session(self, title: str = "新对话", project_path: str = None) -> Dict:
        """
        创建新会话

        Args:
            title: 会话标题
            project_path: 关联的项目路径

        Returns:
            会话字典
        """
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "title": title,
            "project_path": project_path,
            "messages": [],  # LangChain 消息格式
            "created_at": time.time(),
            "updated_at": time.time(),
            "summary": None,
            "metadata": {
                "message_count": 0,
                "tool_call_count": 0,
                "last_active": time.time()
            }
        }

        self.sessions[session_id] = session
        self.current_session_id = session_id

        # 异步保存到存储
        asyncio.create_task(self._save_session_async(session_id))

        logger.info(f"创建新会话：{session_id[:8]}")
        return session

    def get_current_session(self) -> Optional[Dict]:
        """获取当前会话"""
        if not self.current_session_id:
            return None

        session = self.sessions.get(self.current_session_id)
        if not session:
            # 当前会话 ID 无效，重置并创建新会话
            logger.warning(f"当前会话 ID 无效：{self.current_session_id}，创建新会话")
            self.current_session_id = None
            return self.create_session()

        return session

    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取指定会话"""
        return self.sessions.get(session_id)

    def set_current_session(self, session_id: str) -> bool:
        """设置当前会话"""
        if session_id == self.current_session_id:
            return True

        # 验证会话是否存在
        if session_id not in self.sessions:
            logger.warning(f"会话不存在：{session_id}")
            return False

        # 保存当前会话状态
        if self.current_session_id:
            asyncio.create_task(
                self._save_session_async(self.current_session_id))

        self.current_session_id = session_id
        logger.info(f"切换到会话：{session_id[:8]}")
        return True

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id not in self.sessions:
            return False

        # 从内存中删除
        del self.sessions[session_id]

        # 从存储中删除
        self.storage.delete_session(session_id)

        # 如果删除的是当前会话，切换到另一个
        if self.current_session_id == session_id:
            if self.sessions:
                self.current_session_id = list(self.sessions.keys())[0]
            else:
                # 如果没有会话了，创建一个
                self.create_session()

        logger.info(f"删除会话：{session_id[:8]}")
        return True

    # ========== 消息管理（增强版） ==========

    def add_message(self, role: str, content: str, **kwargs) -> Optional[BaseMessage]:
        """
        添加消息到当前会话（支持 LangChain 格式）

        Args:
            role: 角色 (user/assistant/system/tool)
            content: 消息内容
            **kwargs: 其他参数（如 tool_call_id）

        Returns:
            LangChain 消息对象
        """
        session = self.get_current_session()
        if not session:
            logger.error("没有当前会话")
            return None

        # 初始化 metadata（兼容旧会话）
        if "metadata" not in session:
            session["metadata"] = {
                "message_count": 0,
                "tool_call_count": 0,
                "last_active": time.time()
            }

        # 转换为 LangChain 消息格式
        message = self._create_langchain_message(role, content, **kwargs)
        if not message:
            return None

        # 添加到消息列表
        session["messages"].append(message)
        session["updated_at"] = time.time()
        session["metadata"]["message_count"] += 1
        session["metadata"]["last_active"] = time.time()

        # 如果是第一条用户消息，更新标题
        user_messages = [m for m in session["messages"]
                         if isinstance(m, HumanMessage)]
        if len(user_messages) == 1 and role == "user":
            session["title"] = content[:30] + \
                ("..." if len(content) > 30 else "")

        # 检查是否需要截断
        self._manage_context_window(session)

        # 异步保存
        asyncio.create_task(self._save_session_async(session["id"]))

        return message

    def add_tool_message(self, tool_call_id: str, content: str, tool_name: str = "") -> Optional[ToolMessage]:
        """
        添加工具执行结果消息
        
        Args:
            tool_call_id: 工具调用 ID
            content: 工具执行结果
            tool_name: 工具名称
            
        Returns:
            ToolMessage 对象
        """
        session = self.get_current_session()
        if not session:
            return None

        # 初始化 metadata（兼容旧会话）
        if "metadata" not in session:
            session["metadata"] = {
                "message_count": 0,
                "tool_call_count": 0,
                "last_active": time.time()
            }

        # 添加工具名称到内容开头
        if tool_name:
            content = f"[{tool_name}]\n{content}"

        message = ToolMessage(content=content, tool_call_id=tool_call_id)
        session["messages"].append(message)
        session["metadata"]["tool_call_count"] += 1

        asyncio.create_task(self._save_session_async(session["id"]))

        return message

    def update_message(self, index: int, content: str, completed: bool = False) -> None:
        """更新指定索引的消息"""
        session = self.get_current_session()
        if not session or index >= len(session["messages"]):
            return

        msg = session["messages"][index]
        if hasattr(msg, 'content'):
            msg.content = content

        # 添加 completed 标记到消息的 metadata
        if not hasattr(msg, 'additional_kwargs'):
            msg.additional_kwargs = {}
        msg.additional_kwargs['completed'] = completed

        session["updated_at"] = time.time()
        asyncio.create_task(self._save_session_async(session["id"]))

    def get_messages(self, session_id: str = None) -> List[BaseMessage]:
        """
        获取指定会话的消息列表（LangChain 格式）

        Args:
            session_id: 会话 ID，None 表示当前会话

        Returns:
            LangChain 消息列表
        """
        if session_id:
            session = self.get_session(session_id)
        else:
            session = self.get_current_session()

        if not session:
            return []

        return session["messages"].copy()

    def get_messages_for_llm(self, limit: int = None) -> List[BaseMessage]:
        """
        获取发送给 LLM 的消息列表

        Args:
            limit: 限制消息数量（从后往前）

        Returns:
            LangChain 消息列表
        """
        session = self.get_current_session()
        if not session:
            return []

        messages = session["messages"].copy()

        # 限制消息数量（保留最新的）
        if limit:
            messages = messages[-limit:]

        return messages

    def clear_messages(self, keep_system: bool = True) -> bool:
        """
        清空当前会话消息（保留元数据）

        Args:
            keep_system: 是否保留系统消息

        Returns:
            是否成功
        """
        session = self.get_current_session()
        if not session:
            return False

        if keep_system:
            # 保留系统消息
            session["messages"] = [m for m in session["messages"]
                                   if isinstance(m, SystemMessage)]
        else:
            session["messages"] = []

        session["updated_at"] = time.time()
        session["metadata"]["message_count"] = len(session["messages"])

        asyncio.create_task(self._save_session_async(session["id"]))

        logger.info("已清空会话消息")
        return True

    # ========== 会话摘要 ==========

    def get_session_summary(self, session_id: str) -> Optional[str]:
        """获取会话摘要"""
        session = self.get_session(session_id)
        if not session:
            return None
        return session.get("summary")

    def set_session_summary(self, session_id: str, summary: str) -> bool:
        """设置会话摘要"""
        session = self.get_session(session_id)
        if not session:
            return False

        session["summary"] = summary
        self.storage.save_session_summary(session_id, summary)
        return True

    def generate_summary(self, session_id: str) -> Optional[str]:
        """根据对话内容生成摘要"""
        session = self.get_session(session_id)
        if not session:
            return None

        messages = session.get("messages", [])
        if not messages:
            return "暂无对话内容"

        # 提取关键信息生成摘要
        user_messages = [m for m in messages if isinstance(m, HumanMessage)]
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]

        # 简单的摘要策略
        summary_lines = [
            f"# 对话摘要",
            f"",
            f"**创建时间**: {self._format_timestamp(session['created_at'])}",
            f"**最后更新**: {self._format_timestamp(session['updated_at'])}",
            f"**对话轮次**: {len(messages)} 条消息",
            f"**用户提问**: {len(user_messages)} 次",
            f"**AI 回复**: {len(ai_messages)} 次",
            f"**工具调用**: {len(tool_messages)} 次",
            f"",
            f"## 对话概要",
            f""
        ]

        # 如果第一条用户消息存在，作为主题
        if user_messages:
            first_topic = user_messages[0].content[:100]
            if len(user_messages[0].content) > 100:
                first_topic += "..."
            summary_lines.append(f"**主题**: {first_topic}")
            summary_lines.append("")

        # 列出主要话题（前 5 条用户消息）
        if len(user_messages) > 1:
            summary_lines.append("**主要话题**:")
            for i, msg in enumerate(user_messages[:5], 1):
                topic = msg.content[:50].replace("\n", " ")
                if len(msg.content) > 50:
                    topic += "..."
                summary_lines.append(f"{i}. {topic}")

        summary = "\n".join(summary_lines)
        session["summary"] = summary

        # 保存摘要
        self.storage.save_session_summary(session_id, summary)

        return summary

    # ========== 工具方法 ==========

    def _create_langchain_message(self, role: str, content: str, **kwargs) -> Optional[BaseMessage]:
        """创建 LangChain 消息对象"""
        if role == "user":
            return HumanMessage(content=content)
        elif role == "assistant":
            return AIMessage(content=content)
        elif role == "system":
            return SystemMessage(content=content)
        elif role == "tool":
            tool_call_id = kwargs.get("tool_call_id", "")
            return ToolMessage(content=content, tool_call_id=tool_call_id)
        else:
            logger.warning(f"未知角色：{role}")
            return None

    def _deserialize_messages(self, messages: List[Dict]) -> List[BaseMessage]:
        """从序列化格式（数据库格式）恢复 LangChain 消息"""
        result = []
        for msg_dict in messages:
            # 支持两种格式：数据库格式（role）和序列化格式（type）
            role = msg_dict.get("role", "")
            msg_type = msg_dict.get("type", "")
            content = msg_dict.get("content", "")
            tool_call_id = msg_dict.get("tool_call_id", "")

            # 优先使用 role 字段（数据库格式）
            if role == "user" or msg_type == "HumanMessage":
                result.append(HumanMessage(content=content))
            elif role == "assistant" or msg_type == "AIMessage":
                result.append(AIMessage(content=content))
            elif role == "system" or msg_type == "SystemMessage":
                result.append(SystemMessage(content=content))
            elif role == "tool" or msg_type == "ToolMessage":
                result.append(ToolMessage(content=content, tool_call_id=tool_call_id))

        return result

    def _serialize_messages(self, messages: List[BaseMessage]) -> List[Dict]:
        """将 LangChain 消息转换为可序列化格式"""
        result = []
        for msg in messages:
            msg_dict = {
                "type": type(msg).__name__,
                "content": msg.content,
            }
            if isinstance(msg, ToolMessage):
                msg_dict["tool_call_id"] = msg.tool_call_id
            result.append(msg_dict)
        return result

    def _manage_context_window(self, session: Dict):
        """管理上下文窗口，防止消息过多"""
        messages = session["messages"]

        # 初始化 metadata（兼容旧会话）
        if "metadata" not in session:
            session["metadata"] = {
                "message_count": len(messages),
                "tool_call_count": 0,
                "last_active": time.time()
            }

        # 如果消息数超过阈值
        if len(messages) > self.max_context_messages:
            # 保留系统消息和最新的消息
            system_messages = [
                m for m in messages if isinstance(m, SystemMessage)]
            recent_messages = messages[-(self.max_context_messages -
                                         len(system_messages)):]

            session["messages"] = system_messages + recent_messages
            logger.debug(f"上下文窗口管理：保留 {len(session['messages'])} 条消息")

    async def _save_session_async(self, session_id: str):
        """异步保存会话"""
        try:
            session = self.sessions.get(session_id)
            if session:
                # 转换为可序列化格式（确保消息是字典）
                serializable_session = self._serialize_session(session)
                
                # 验证消息格式
                for msg in serializable_session.get("messages", []):
                    if not isinstance(msg, dict):
                        logger.error(f"消息格式错误：{type(msg)}")
                        raise TypeError(f"消息应该是 dict，实际是 {type(msg)}")
                    if "role" not in msg or "content" not in msg:
                        logger.error(f"消息缺少必要字段：{msg.keys()}")
                        raise ValueError(f"消息缺少 role 或 content 字段")
                
                self.storage.save_session(serializable_session)
        except Exception as e:
            logger.error(f"保存会话失败：{e}")

    def _serialize_session(self, session: Dict) -> Dict:
        """将会话转换为可序列化格式（用于数据库存储）"""
        # 深拷贝避免修改原数据
        serialized = copy.deepcopy(session)

        # 转换 LangChain 消息为字典格式（带 role 字段）
        serialized["messages"] = []
        for msg in session["messages"]:
            msg_dict = {
                "role": self._get_message_role(msg),
                "content": msg.content,
                "timestamp": time.time()
            }
            # 如果是 ToolMessage，添加 tool_call_id
            if isinstance(msg, ToolMessage):
                msg_dict["tool_call_id"] = msg.tool_call_id
                msg_dict["role"] = "tool"
            serialized["messages"].append(msg_dict)

        return serialized

    def _get_message_role(self, msg: BaseMessage) -> str:
        """获取 LangChain 消息对应的 role 字符串"""
        if isinstance(msg, HumanMessage):
            return "user"
        elif isinstance(msg, AIMessage):
            return "assistant"
        elif isinstance(msg, SystemMessage):
            return "system"
        elif isinstance(msg, ToolMessage):
            return "tool"
        else:
            return "unknown"

    def _format_timestamp(self, timestamp: float) -> str:
        """格式化时间戳"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def get_all_sessions(self) -> List[Dict]:
        """获取所有会话"""
        return list(self.sessions.values())

    def clear_all_sessions(self) -> None:
        """清空所有会话（保留一个）"""
        if self.sessions:
            # 保留最新的会话
            sorted_sessions = sorted(
                self.sessions.values(),
                key=lambda s: s.get("updated_at", 0),
                reverse=True
            )
            latest_session = sorted_sessions[0]

            # 清空其他会话
            session_ids = list(self.sessions.keys())
            for session_id in session_ids:
                if session_id != latest_session["id"]:
                    self.delete_session(session_id)

            self.current_session_id = latest_session["id"]
            logger.info("清空所有会话")

    def to_dict(self) -> Dict:
        """转换为字典格式（用于序列化）"""
        # 转换消息为可序列化格式
        sessions_data = []
        for session in self.sessions.values():
            serialized = self._serialize_session(session)
            sessions_data.append(serialized)

        return {
            "sessions": sessions_data,
            "current_session_id": self.current_session_id
        }

    def from_dict(self, data: Dict) -> None:
        """从字典加载数据"""
        sessions_data = data.get("sessions", [])
        for session_dict in sessions_data:
            session_id = session_dict.get("id")
            if session_id:
                # 转换消息为 LangChain 格式
                session_dict["messages"] = self._deserialize_messages(
                    session_dict.get("messages", []))
                self.sessions[session_id] = session_dict

        self.current_session_id = data.get("current_session_id")
        logger.info(f"加载了 {len(self.sessions)} 个会话")
